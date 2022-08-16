from datetime import datetime

local_homedir = "/home/anomond"
remote_homedir = "/home/anomond"
sweeper_parameters_file = "sweeper_parameters.yaml"

ref_execution_timestamp = None
execution_expe_dir = None


def global_dir_expe(expe_name):
    return f"{local_homedir}/concerto-d-execution-{expe_name}"


def initialize_execution_expe_dir():
    global ref_execution_timestamp
    global execution_expe_dir
    ref_execution_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    execution_expe_dir = f"{global_dir_expe}/execution-{ref_execution_timestamp}"

