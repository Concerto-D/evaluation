import os
from datetime import datetime

all_expes_dir = ""
all_executions_dir = ""

current_expe_dir = None
current_execution_dir = None


def compute_current_expe_dir_from_name(expe_name):
    return f"{all_expes_dir}/experiment-{expe_name}-dir"


def initialize_all_dirs(expe_name: str, all_expes_dir_str: str, all_executions_dir_str: str):
    global all_expes_dir
    global all_executions_dir
    all_expes_dir = all_expes_dir_str
    all_executions_dir = all_executions_dir_str
    experiment_results_dir = compute_current_expe_dir_from_name(expe_name)
    os.makedirs(f"{experiment_results_dir}/experiment_logs", exist_ok=True)


def initialize_current_dirs(expe_name):
    """
    Initialization of the experiments directories.
    <all_expes_dir>: global dir on the host where all the executions of expe_name are executed.
    <all_executions_dir>: global dir on the remote infrastructure where all the executions are executed (here on G5K)
    <current_expe_dir>: specific local dir of the execution of parameters
    <current_execution_dir>: specific remote dir of the execution of parameters
    """
    global current_execution_dir
    global current_expe_dir
    ref_execution_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    execution_expe_dir = f"execution-{expe_name}-{ref_execution_timestamp}"
    current_execution_dir = f"{all_executions_dir}/{execution_expe_dir}"
    current_expe_dir = f"{compute_current_expe_dir_from_name(expe_name)}/{execution_expe_dir}"
