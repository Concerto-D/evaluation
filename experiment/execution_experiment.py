import os
import sys

import yaml
import infrastructure_reservation
from experiment import globals_variables, log_experiment, experiment_controller

if __name__ == '__main__':
    # Extraction des paramètres
    configuration_expe_file_path = sys.argv[1]
    with open(configuration_expe_file_path) as f:
        expe_parameters = yaml.safe_load(f)
    (
        expe_name,
        version_concerto_d,
        local_project_dir,
        remote_project_dir
    ) = expe_parameters["global_parameters"].values()

    # Création du dossier de l'expérience et du dossier pour les logs
    globals_variables.local_project_dir = local_project_dir
    globals_variables.remote_project_dir = remote_project_dir
    global_local_dir_expe = globals_variables.global_local_dir_expe(expe_name)
    os.makedirs(f"{global_local_dir_expe}/experiment_logs", exist_ok=True)

    # Init logging
    log_experiment.initialize_logging(expe_name)
    log = log_experiment.log

    log.debug(f"Start {expe_name}")
    roles_concerto_d = infrastructure_reservation.create_reservation_for_concerto_d(
        version_concerto_d,
        expe_parameters["reservation_parameters"]
    )

    # Execution experiment
    params_to_sweep = expe_parameters["sweeper_parameters"]
    experiment_controller.create_and_run_sweeper(
        expe_name,
        expe_parameters["reservation_parameters"]["cluster"],
        version_concerto_d,
        params_to_sweep,
        roles_concerto_d
    )