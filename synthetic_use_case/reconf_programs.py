import logging
import os
import sys
from typing import Tuple, Dict, Optional
import argparse

import yaml

from concerto import time_logger, global_variables, debug_logger


def get_assembly_parameters(args) -> Tuple[Dict, float, bool, Optional[str], str, str, str, int, Optional[int], str, float, str]:
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file_path")
    parser.add_argument("uptime_duration", type=float)
    parser.add_argument("waiting_rate")
    parser.add_argument("timestamp_log_dir")
    parser.add_argument("execution_expe_dir")
    parser.add_argument("version_concerto_d")
    parser.add_argument("reconfiguration_name")
    parser.add_argument("nb_concerto_nodes", type=int)
    parser.add_argument("--dep_num", type=int)
    parser.add_argument("--uptimes_nodes_file_path")
    parser.add_argument("--execution_start_time", type=float)
    parser.add_argument("--debug_current_uptime_and_overlap")
    (
        config_file_path,
        uptime_duration,
        waiting_rate,
        timestamp_log_dir,
        execution_expe_dir,
        version_concerto_d,
        reconfiguration_name,
        nb_concerto_nodes,
        dep_num,
        uptimes_nodes_file_path,
        execution_start_time,
        debug_current_uptime_and_overlap
     ) = parser.parse_args().__dict__.values()

    with open(config_file_path, "r") as f:
        loaded_config = yaml.safe_load(f)

    return loaded_config, uptime_duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num, uptimes_nodes_file_path, execution_start_time, debug_current_uptime_and_overlap


def initialize_reconfiguration():
    # TODO: remove timestamp_log_dir
    config_dict, duration, waiting_rate, timestamp_log_dir, execution_expe_dir, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num, uptimes_nodes_file_path, execution_start_time, debug_current_uptime_and_overlap = get_assembly_parameters(sys.argv)

    # Set assembly name
    if version_concerto_d == "central":
        assembly_name = "server-clients"
    else:
        assembly_name = f"dep{dep_num}" if dep_num is not None else "server"

    # Init log and dirs
    time_logger.init_time_log_dir(assembly_name)
    os.makedirs(f"{execution_expe_dir}/reprise_configs", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/communication_cache", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/logs", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/archives_reprises", exist_ok=True)
    os.makedirs(f"{execution_expe_dir}/finished_reconfigurations", exist_ok=True)
    logging.basicConfig(filename=f"{execution_expe_dir}/logs/logs_{assembly_name}.txt", format=f"{assembly_name} - %(asctime)s %(message)s", filemode="a+")
    debug_logger.set_stdout_formatter(assembly_name)
    global_variables.execution_expe_dir = execution_expe_dir

    params_to_log = {
        "duration": duration,
        "waiting_rate": waiting_rate,
        "timestamp_log_dir": timestamp_log_dir,
        "execution_expe_dir": execution_expe_dir,
        "version_concerto_d": version_concerto_d,
        "reconfiguration_name": reconfiguration_name,
        "nb_concerto_nodes": nb_concerto_nodes,
        "dep_num": dep_num,
        "uptimes_nodes_file_path": uptimes_nodes_file_path,
        "execution_start_time": execution_start_time
    }
    debug_logger.log.debug(f"Initialization complete, script parameters: {params_to_log}")
    debug_logger.log.debug(f"Current round: {debug_current_uptime_and_overlap.strip()}")
    return config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num, uptimes_nodes_file_path, execution_start_time
