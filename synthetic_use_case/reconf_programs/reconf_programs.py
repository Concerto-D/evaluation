import logging
import os
import sys
from typing import Tuple, Dict, Optional

import yaml

from concerto import time_logger, global_variables, debug_logger


def get_assembly_parameters(args) -> Tuple[Dict, float, bool, Optional[str], str, str, str, int, Optional[int]]:
    config_file_path = args[1]
    with open(config_file_path, "r") as f:
        loaded_config = yaml.safe_load(f)
    uptime_duration = float(args[2])
    waiting_rate = args[3]
    timestamp_log_dir = args[4]
    execution_expe_dir = args[5]
    version_concerto_d = args[6]
    reconfiguration_name = args[7]
    nb_concerto_nodes = int(args[8])
    dep_num = int(args[9]) if len(args) > 9 else None
    return loaded_config, uptime_duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num


def initialize_reconfiguration():
    config_dict, duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num = get_assembly_parameters(sys.argv)

    # Set assembly name
    if version_concerto_d == "central":
        assembly_name = "central_controller"
    else:
        assembly_name = f"dep{dep_num}" if dep_num is not None else "server"

    # Init log and dirs
    time_logger.init_time_log_dir(assembly_name, timestamp_log_dir=timestamp_log_dir)
    os.makedirs(f"{execution_expe_dir}/reprise_configs", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/communication_cache", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/logs", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/archives_reprises", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/finished_reconfigurations", exist_ok=True)
    logging.basicConfig(filename=f"{execution_expe_dir}/logs/logs_{assembly_name}.txt", format=f"{assembly_name} - %(asctime)s %(message)s", filemode="a+")
    debug_logger.set_stdout_formatter(assembly_name)
    global_variables.execution_expe_dir = execution_expe_dir

    return config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num
