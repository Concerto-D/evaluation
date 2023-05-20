import sys
import traceback

import yaml

import infrastructure_reservation
from experiment import globals_variables, log_experiment, experiment_controller, infrastructure_configuration, \
    compute_results, email_sender


def extract_parameters(configuration_expe_file_path: str):
    with open(configuration_expe_file_path) as f:
        expe_params = yaml.safe_load(f)

    return expe_params["global_parameters"], expe_params["reservation_parameters"], expe_params["email_parameters"], expe_params["sweeper_parameters"]


def main(configuration_expe_file_path):
    email_parameters, environment, expe_name, local_expe_res_dir, log, provider, reservation_params, roles_concerto_d, send_mail_after_all_expes, sweeper_params, use_case_name, version_concerto_d = initialize_expe(configuration_expe_file_path)

    # Create sweeper
    sweeper = experiment_controller.create_param_sweeper(expe_name, sweeper_params)

    # Run sweeper
    log.debug("------------------------ Execution of experiments start ------------------------")
    parameter = sweeper.get_next()
    while parameter:
        execution_dir_name = ""
        try:
            execution_dir_name, results = execute_expe(environment, expe_name, parameter, reservation_params, roles_concerto_d, use_case_name, version_concerto_d)
            sweeper.done(parameter)
            log.debug(f"Parameter {parameter} done")
            log.debug(f"State of the sweeper: {sweeper}")
        except Exception as e:
            sweeper.skip(parameter)
            log.debug("Experiment FAILED")
            log.debug(traceback.format_exc())
            log.debug(f"Skipping experiment with parameters {parameter}, execution_dir_name: {execution_dir_name}")
            log.debug("Not yielding result")
        finally:
            parameter = sweeper.get_next()

    # Destroy infrastructure reservation after all experiments completed
    log.debug("--------- All experiments dones ---------")
    destroy_reservation = reservation_params.get("destroy_reservation", "True") == "True"
    if destroy_reservation and environment == "remote":
        log.debug("------------ Destroy infra -------------")
        provider.destroy()
    else:
        log.debug("-------------Do not destroy infra ------")

    if environment != "local" and send_mail_after_all_expes == "True":
        log.debug("--------- Send mail --------------------------")
        email_sender.send_email_expe_finished(expe_name, str(sweeper), sweeper_params, local_expe_res_dir, email_parameters)
    else:
        log.debug("--------- Do not send mail --------------------------")


def initialize_expe(configuration_expe_file_path, testing=False):
    # Extraction des paramètres
    global_params, reservation_params, email_parameters, sweeper_params = extract_parameters(
        configuration_expe_file_path)
    # Extract parametres globaux
    (
        expe_name,
        environment,
        version_concerto_d,
        use_case_name,
        all_expes_dir,
        all_executions_dir,
        fetch_experiment_results,
        local_expe_res_dir,
        send_mail_after_all_expes
    ) = global_params.values()
    # Création du dossier de l'expérience et du dossier pour les logs
    globals_variables.initialize_all_dirs(expe_name, all_expes_dir, all_executions_dir)

    # Init logging
    log_experiment.initialize_logging(expe_name, file_only=testing)
    log = log_experiment.log
    # Infrastructure reservation
    roles_concerto_d, provider = infrastructure_reservation.create_infrastructure_reservation(
        expe_name,
        environment,
        reservation_params,
        version_concerto_d,
        use_case_name
    )
    # Infrastructure configuration
    infrastructure_configuration.configure_infrastructure(version_concerto_d, roles_concerto_d, environment,
                                                          use_case_name)
    return email_parameters, environment, expe_name, local_expe_res_dir, log, provider, reservation_params, roles_concerto_d, send_mail_after_all_expes, sweeper_params, use_case_name, version_concerto_d


def execute_expe(environment, expe_name, parameter, reservation_params, roles_concerto_d, use_case_name, version_concerto_d):
    log = log_experiment.log
    uptimes, transitions_times, waiting_rate, id_run = parameter.values()
    log.debug("----- Starting experiment ---------")
    log.debug("-- Expe parameters --")
    log.debug(f"Uptimes: {uptimes}")
    log.debug(f"Transitions times: {transitions_times}")
    log.debug(f"Waiting rate: {waiting_rate}")
    log.debug(f"Id: {id_run}")
    log.debug("---------------------")

    # Initialize expe dirs and get uptimes nodes
    log.debug("-------------- Initialising dirs ---------------")
    cluster_name = reservation_params["cluster"] if environment == "remote" else environment
    execution_dir_name = globals_variables.initialize_current_dirs(
        expe_name,
        version_concerto_d,
        transitions_times,
        uptimes,
        waiting_rate,
        cluster_name
    )
    log.debug("-------------------- Launching experiment -----------------------")
    finished_reconfs_by_reconf_name = experiment_controller.launch_experiment_with_params(
        expe_name,
        version_concerto_d,
        reservation_params["nb_dependencies"] + reservation_params["nb_servers"] + reservation_params[
            "nb_server_clients"]
        + reservation_params["nb_provider_nodes"] + reservation_params["nb_chained_nodes"],
        uptimes,
        transitions_times,
        waiting_rate,
        environment,
        roles_concerto_d,
        use_case_name,
        id_run
    )
    log.debug("------------------ Saving expe metadata --------------------------")
    compute_results.save_expe_metadata(
        finished_reconfs_by_reconf_name,
        version_concerto_d,
        transitions_times,
        uptimes,
        waiting_rate,
        reservation_params["cluster"],
    )
    log.debug("----------------- Compute results from execution dir -----------")
    experiment_dir = globals_variables.compute_current_expe_dir_from_name(expe_name)
    log.debug(f"Experiment dir: {experiment_dir}")
    log.debug(f"Execution dir name: {execution_dir_name}")
    assemblies_names = []
    if reservation_params["nb_servers"] == 1:
        assemblies_names.append("server")
    for i in range(reservation_params["nb_dependencies"]):
        assemblies_names.append(f"dep{i}")
    if reservation_params["nb_server_clients"] == 1:
        assemblies_names.append("server-clients")
    if reservation_params["nb_provider_nodes"] == 1:
        assemblies_names.append("provider_node")
    for i in range(reservation_params["nb_chained_nodes"]):
        assemblies_names.append(f"chained_node{i}")
    log.debug(f"List assemblies names to compute metrics from: {assemblies_names}")
    results = compute_results.compute_results_from_dir(expe_name, experiment_dir, execution_dir_name, assemblies_names)
    return execution_dir_name, results


if __name__ == '__main__':
    main(sys.argv[1])
