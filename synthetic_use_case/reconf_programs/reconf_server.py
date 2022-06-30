import logging
import os
import sys
from typing import Tuple, Dict, Optional

from concerto.debug_logger import log

from concerto import time_logger
from concerto.time_logger import TimeToSave
from synthetic_use_case.assemblies.server_assembly import ServerAssembly
import yaml


def get_assembly_parameters(args) -> Tuple[Dict, float, bool, Optional[str]]:
    config_file_path = args[1]
    with open(config_file_path, "r") as f:
        loaded_config = yaml.safe_load(f)
    uptime_duration = float(args[2])
    sleep_when_blocked = args[3] == 2
    timestamp_log_dir = args[4] if len(args) > 4 else None
    return loaded_config, uptime_duration, sleep_when_blocked, timestamp_log_dir


def deploy(sc, nb_deps_tot):
    # _p_id_sync = 0
    sc.add_component("server", sc.server)
    for dep_num in range(nb_deps_tot):
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
    sc.push_b("server", "deploy")
    sc.wait_all()


def update(sc):
    # _p_id_sync = 1
    sc.push_b("server", "suspend")
    sc.wait_all(wait_for_refusing_provide=True)
    sc.push_b("server", "deploy")
    sc.wait_all()


def execute_reconf(config_dict, duration, sleep_when_blocked=True):
    sc = ServerAssembly(config_dict, sleep_when_blocked=sleep_when_blocked)
    sc.set_verbosity(2)
    deploy(sc, config_dict["nb_deps_tot"])
    update(sc)
    sc.execute_reconfiguration_program(duration)


if __name__ == '__main__':
    # TODO Voir si loader la config file prend du temps (comme pour loader
    # le state), car on log the uptime après
    config_dict, duration, sleep_when_blocked, timestamp_log_dir = get_assembly_parameters(sys.argv)
    time_logger.init_time_log_dir("server", timestamp_log_dir=timestamp_log_dir)
    time_logger.log_time_value(TimeToSave.UP_TIME)
    os.makedirs("concerto/logs", exist_ok=True)
    logging.basicConfig(filename="concerto/logs/logs_server.txt", format='%(asctime)s %(message)s', filemode="a+")
    log.debug(f"Working directory: {os.getcwd()}")
    log.debug(f"Python path: {sys.path}")
    execute_reconf(config_dict, duration, sleep_when_blocked=sleep_when_blocked)
    time_logger.log_time_value(TimeToSave.SLEEP_TIME)
