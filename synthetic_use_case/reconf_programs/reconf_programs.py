import logging
import os
import sys
from typing import Tuple, Dict, Optional

import yaml

from concerto import time_logger, global_variables
from concerto.time_logger import TimeToSave


def get_assembly_parameters(args) -> Tuple[Dict, float, bool, Optional[str], str, str, Optional[int]]:
    config_file_path = args[1]
    with open(config_file_path, "r") as f:
        loaded_config = yaml.safe_load(f)
    uptime_duration = float(args[2])
    waiting_rate = args[3]
    timestamp_log_dir = args[4]
    execution_expe_dir = args[5]
    version_concerto_d = args[6]
    dep_num = int(args[7]) if len(args) > 6 else None
    return loaded_config, uptime_duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, dep_num


def initialize_reconfiguration():
    config_dict, duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, dep_num = get_assembly_parameters(sys.argv)
    assembly_name = f"dep{dep_num}" if dep_num is not None else "server"
    time_logger.init_time_log_dir(assembly_name, timestamp_log_dir=timestamp_log_dir)
    time_logger.log_time_value(TimeToSave.UP_TIME)
    os.makedirs(f"{execution_expe_dir}/logs", exist_ok=True)
    logging.basicConfig(filename=f"{execution_expe_dir}/logs/logs_{assembly_name}.txt", format='%(asctime)s %(message)s', filemode="a+")
    global_variables.execution_expe_dir = execution_expe_dir

    return config_dict, duration, waiting_rate, version_concerto_d, dep_num