import os
import sys

import yaml
from enoslib import Host

import infrastructure_reservation
from experiment import globals_variables, log_experiment, experiment_controller

if __name__ == '__main__':
    # Extraction des paramètres
    configuration_expe_file_path = sys.argv[1]
    with open(configuration_expe_file_path) as f:
        expe_parameters = yaml.safe_load(f)
    (
        expe_name,
        environment,
        version_concerto_d,
        all_experiments_results_dir,
        g5k_executions_expe_logs_dir
    ) = expe_parameters["global_parameters"].values()

    # Création du dossier de l'expérience et du dossier pour les logs
    globals_variables.all_experiments_results_dir = all_experiments_results_dir
    globals_variables.g5k_executions_expe_logs_dir = g5k_executions_expe_logs_dir
    experiment_results_dir = globals_variables.experiment_results_dir(expe_name)
    os.makedirs(f"{experiment_results_dir}/experiment_logs", exist_ok=True)

    # Init logging
    log_experiment.initialize_logging(expe_name)
    log = log_experiment.log
    roles_concerto_d = None
    nb_concerto_nodes = expe_parameters["reservation_parameters"]["nb_concerto_nodes"]
    if environment == "remote":
        log.debug(f"Start {expe_name}")
        roles_concerto_d, provider = infrastructure_reservation.create_reservation_for_concerto_d(
            version_concerto_d,
            expe_parameters["reservation_parameters"],
            environment
        )
    else:
        roles_concerto_d = {
            "server": Host("localhost"),
            **{f"dep{dep_num}": Host("localhost") for dep_num in range(nb_concerto_nodes - 1)},
            "zenoh_routers": Host("localhost")
        }
        provider = None

    # Execution experiment
    params_to_sweep = expe_parameters["sweeper_parameters"]
    destroy_reservation = expe_parameters["reservation_parameters"].get("destroy_reservation", "True") == "True"
    experiment_controller.create_and_run_sweeper(
        expe_name,
        expe_parameters["reservation_parameters"]["cluster"],
        version_concerto_d,
        nb_concerto_nodes,
        params_to_sweep,
        environment,
        roles_concerto_d,
        destroy_reservation,
        provider
    )
