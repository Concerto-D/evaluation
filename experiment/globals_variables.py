import os
from datetime import datetime

local_homedir = "/home/aomond/implementations/concerto-d-projects"
remote_homedir = "/home/anomond"
sweeper_parameters_file = "sweeper_parameters.yaml"

ref_execution_timestamp = None
remote_execution_expe_dir = None
local_execution_expe_dir = None


def global_local_dir_expe(expe_name):
    return f"{local_homedir}/global-{expe_name}-dir"


def initialize_remote_execution_expe_dir_name(expe_name):
    global ref_execution_timestamp
    global remote_execution_expe_dir
    global local_execution_expe_dir
    ref_execution_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    execution_expe_dir = f"execution-{expe_name}-{ref_execution_timestamp}"
    remote_execution_expe_dir = f"{remote_homedir}/{execution_expe_dir}"
    local_execution_expe_dir = f"{global_local_dir_expe(expe_name)}/{execution_expe_dir}"

