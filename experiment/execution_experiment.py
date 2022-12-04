import sys
import traceback

import yaml

import infrastructure_reservation
from experiment import globals_variables, log_experiment, experiment_controller, infrastructure_configuration, \
    compute_results


def extract_parameters(configuration_expe_file_path: str):
    with open(configuration_expe_file_path) as f:
        expe_params = yaml.safe_load(f)

    return expe_params["global_parameters"], expe_params["reservation_parameters"], expe_params["sweeper_parameters"]


if __name__ == '__main__':
    # Extraction des paramètres
    configuration_expe_file_path = sys.argv[1]
    global_params, reservation_params, sweeper_params = extract_parameters(configuration_expe_file_path)

    # Extract parametres globaux
    (
        expe_name,
        environment,
        version_concerto_d,
        all_expes_dir,
        all_executions_dir
    ) = global_params.values()

    # Création du dossier de l'expérience et du dossier pour les logs
    globals_variables.initialize_all_dirs(expe_name, all_expes_dir, all_executions_dir)

    # Init logging
    log_experiment.initialize_logging(expe_name)
    log = log_experiment.log

    # Infrastructure reservation
    roles_concerto_d, provider = infrastructure_reservation.create_infrastructure_reservation(expe_name, environment, reservation_params)

    # Infrastructure configuration
    if environment == "remote":
        infrastructure_configuration.configure_infrastructure(version_concerto_d, roles_concerto_d, environment)

    # Create sweeper
    sweeper = experiment_controller.create_param_sweeper(expe_name, sweeper_params)

    # Run sweeper
    destroy_reservation = reservation_params.get("destroy_reservation", "True") == "True"
    parameter = sweeper.get_next()
    while parameter:
        try:
            finished_reconfs_by_reconf_name = experiment_controller.launch_experiment_with_params(
                expe_name,
                version_concerto_d,
                reservation_params["nb_concerto_nodes"],
                parameter["uptimes"],
                parameter["transitions_times"],
                parameter["waiting_rate"],
                environment,
                roles_concerto_d,
                parameter["id"]
            )

            compute_results.save_expe_metadata(
                finished_reconfs_by_reconf_name,
                version_concerto_d,
                parameter["transitions_times"],
                parameter["uptimes"],
                parameter["waiting_rate"],
                reservation_params["cluster"],
            )
            compute_results.compute_from_expe_dir(f"experiment-{expe_name}-dir", nb_concerto_nodes=reservation_params["nb_concerto_nodes"])

            sweeper.done(parameter)
            log.debug(f"Parameter {parameter} done")
            log.debug(f"State of the sweeper: {sweeper}")
        except Exception as e:
            sweeper.skip(parameter)
            log.debug("Experiment FAILED")
            log.debug(e)
            log.debug(f"Skipping experiment with parameters {parameter}")
            traceback.print_exc()
        finally:
            parameter = sweeper.get_next()

    # Destroy infrastructure reservation after all experiments completed
    log.debug("--------- All experiments dones ---------")
    if destroy_reservation and environment == "remote":
        log.debug("Destroy reservation == True, destroy reserved infra")
        provider.destroy()
