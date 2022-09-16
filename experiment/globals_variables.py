import os
from datetime import datetime

all_experiments_results_dir = ""
g5k_executions_expe_logs_dir = ""

local_execution_params_dir = None
g5k_execution_params_dir = None


def experiment_results_dir(expe_name):
    return f"{all_experiments_results_dir}/experiment-{expe_name}-dir"


def initialize_remote_execution_expe_dir_name(expe_name):
    """
    Initialization of the experiments directories.
    <all_experiments_results_dir>: global dir on the host where all the executions of expe_name are executed.
    <g5k_executions_expe_logs_dir>: global dir on the remote infrastructure where all the executions are executed (here on G5K)
    <local_execution_params_dir>: specific local dir of the execution of parameters
    <g5k_execution_params_dir>: specific remote dir of the execution of parameters
    """
    global g5k_execution_params_dir
    global local_execution_params_dir
    ref_execution_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    execution_expe_dir = f"execution-{expe_name}-{ref_execution_timestamp}"
    g5k_execution_params_dir = f"{g5k_executions_expe_logs_dir}/{execution_expe_dir}"
    local_execution_params_dir = f"{experiment_results_dir(expe_name)}/{execution_expe_dir}"
