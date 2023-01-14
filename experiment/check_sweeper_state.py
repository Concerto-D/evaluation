import sys

from experiment import globals_variables, execution_experiment, experiment_controller, log_experiment

if __name__ == "__main__":
    configuration_expe_file_path = sys.argv[1]
    global_params, reservation_params, sweeper_params = execution_experiment.extract_parameters(configuration_expe_file_path)
    (
        expe_name,
        environment,
        version_concerto_d,
        all_expes_dir,
        all_executions_dir
    ) = global_params.values()
    log_experiment.initialize_logging(expe_name, stdout_only=True)
    globals_variables.all_expes_dir = all_expes_dir
    sweeper = experiment_controller.create_param_sweeper(expe_name, sweeper_params)
    print(sweeper)
