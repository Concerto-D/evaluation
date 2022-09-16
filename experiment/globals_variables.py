import os
from datetime import datetime

local_project_dir = "/home/aomond/implementations/concerto-d-projects"
remote_project_dir = "/home/anomond"
sweeper_parameters_file = "sweeper_parameters.yaml"

remote_execution_expe_dir = None
local_execution_expe_dir = None


def global_local_dir_expe(expe_name):
    return f"{local_project_dir}/global-{expe_name}-dir"


def initialize_remote_execution_expe_dir_name(expe_name):
    global remote_execution_expe_dir
    global local_execution_expe_dir
    ref_execution_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    execution_expe_dir = f"execution-{expe_name}-{ref_execution_timestamp}"
    remote_execution_expe_dir = f"{remote_project_dir}/{execution_expe_dir}"
    local_execution_expe_dir = f"{global_local_dir_expe(expe_name)}/{execution_expe_dir}"
