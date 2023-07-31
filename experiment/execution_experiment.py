import sys
import traceback

import yaml

import infrastructure_reservation
from experiment import globals_variables, log_experiment, experiment_controller, infrastructure_configuration, \
    compute_results, email_sender, concerto_d_g5k


def extract_parameters(configuration_expe_file_path: str):
    with open(configuration_expe_file_path) as f:
        expe_params = yaml.safe_load(f)

    return expe_params["global_parameters"], expe_params["reservation_parameters"], expe_params["use_case_nodes"], expe_params["email_parameters"], expe_params["sweeper_parameters"]


def main(configuration_expe_file_path):
    (
        email_parameters,
        environment,
        expe_name,
        local_expe_res_dir,
        log,
        provider,
        reservation_params,
        roles_concerto_d,
        send_mail_after_all_expes,
        sweeper_params,
        use_case_name,
        version_concerto_d,
        use_case_nodes_items
    ) = initialize_expe(configuration_expe_file_path)

    # Create sweeper
    sweeper = experiment_controller.create_param_sweeper(expe_name, sweeper_params)

    # Run sweeper
    log.debug("------------------------ Execution of experiments start ------------------------")
    parameter = sweeper.get_next()
    while parameter:
        log.debug(f"Starting experiment with parameter: {parameter}")
        execution_dir_name = ""
        try:
            if use_case_name == "openstack" and use_case_nodes_items.get("include_planner", False):
                concerto_d_g5k.execute_planner(roles_concerto_d, parameter["nb_scaling_nodes"], parameter["id"], expe_name)
            if use_case_name == "str_cps" and use_case_nodes_items.get("include_planner", False):
                concerto_d_g5k.execute_planner_str_cps(roles_concerto_d, parameter["nb_scaling_nodes"], parameter["id"], expe_name)
            if use_case_nodes_items.get("include_execution", False):
                execution_dir_name, results = execute_expe(environment, expe_name, parameter, reservation_params, roles_concerto_d, use_case_name, version_concerto_d, use_case_nodes_items)
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
    (
        global_params,
        reservation_params,
        use_case_nodes,
        email_parameters,
        sweeper_params
    ) = extract_parameters(configuration_expe_file_path)

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
    log_experiment.initialize_logging(expe_name, stdout_only=testing)
    log = log_experiment.log
    log.debug("Log initialized")

    # Infrastructure reservation
    roles_concerto_d, provider = infrastructure_reservation.create_infrastructure_reservation(
        expe_name,
        environment,
        reservation_params,
        use_case_nodes,
        version_concerto_d,
        use_case_name
    )

    # Infrastructure configuration
    infrastructure_configuration.configure_infrastructure(version_concerto_d, roles_concerto_d, environment, use_case_name)

    use_case_nodes_items = use_case_nodes[use_case_name]
    return email_parameters, environment, expe_name, local_expe_res_dir, log, provider, reservation_params, roles_concerto_d, send_mail_after_all_expes, sweeper_params, use_case_name, version_concerto_d, use_case_nodes_items


def execute_expe(environment, expe_name, parameter, reservation_params, roles_concerto_d, use_case_name, version_concerto_d, use_case_nodes_items):
    log = log_experiment.log
    # uptimes, transitions_times, waiting_rate, id_run = parameter.values() TODO: refacto parallel_deps
    uptimes, transitions_times, nb_scaling_sites, id_run = parameter.values()
    log.debug("----- Starting experiment ---------")
    log.debug("-- Expe parameters --")
    log.debug(f"Uptimes: {uptimes}")
    log.debug(f"Transitions times: {transitions_times}")
    log.debug(f"Nb scaling sites: {nb_scaling_sites}")
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
        nb_scaling_sites,
        cluster_name
    )
    duration = use_case_nodes_items["uptime_duration"]

    log.debug("-------------------- Launching experiment -----------------------")

    if version_concerto_d == "central":
        nb_scaling_nodes = use_case_nodes_items["nb_server_clients"]
    elif use_case_name == "parallel_deps":
        nb_scaling_nodes = use_case_nodes_items["nb_dependencies"] + use_case_nodes_items["nb_servers"]
    elif use_case_name in ["openstack", "str_cps"]:
        nb_scaling_nodes = nb_scaling_sites
    else:
        nb_scaling_nodes = use_case_nodes_items["nb_provider_nodes"] + use_case_nodes_items["nb_chained_nodes"]

    finished_reconfs_by_reconf_name = experiment_controller.launch_experiment_with_params(
        expe_name,
        version_concerto_d,
        nb_scaling_nodes,
        uptimes,
        transitions_times,
        environment,
        roles_concerto_d,
        use_case_name,
        duration,
        id_run
    )
    log.debug("------------------ Saving expe metadata --------------------------")
    compute_results.save_expe_metadata(
        finished_reconfs_by_reconf_name,
        version_concerto_d,
        transitions_times,
        uptimes,
        nb_scaling_sites,
        reservation_params["cluster"],
    )
    log.debug("----------------- Compute results from execution dir -----------")
    experiment_dir = globals_variables.compute_current_expe_dir_from_name(expe_name)
    log.debug(f"Experiment dir: {experiment_dir}")
    log.debug(f"Execution dir name: {execution_dir_name}")

    if use_case_name in ["openstack", "str_cps"]:
        assemblies_names = [comp for comp in roles_concerto_d.keys() if comp != "reconfiguring"]
    else:
        assemblies_names = []
        if use_case_nodes_items["nb_servers"] == 1:
            assemblies_names.append("server")
        for i in range(use_case_nodes_items["nb_dependencies"]):
            assemblies_names.append(f"dep{i}")
        if use_case_nodes_items["nb_server_clients"] == 1:
            assemblies_names.append("server-clients")
        if use_case_nodes_items["nb_provider_nodes"] == 1:
            assemblies_names.append("provider_node")
        for i in range(use_case_nodes_items["nb_chained_nodes"]):
            assemblies_names.append(f"chained_node{i}")

    log.debug(f"List assemblies names to compute metrics from: {assemblies_names}")
    results = compute_results.compute_results_from_dir(expe_name, experiment_dir, execution_dir_name, assemblies_names, use_case_name)
    return execution_dir_name, results


if __name__ == '__main__':
    main(sys.argv[1])
