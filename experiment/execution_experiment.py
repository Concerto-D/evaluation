import json
import logging
import math
import os
import shutil
import sys
import time
import traceback
from datetime import datetime
from os.path import exists
from pathlib import Path
from threading import Thread
from typing import List

import yaml
from execo_engine import sweep, ParamSweeper

from experiment import concerto_d_g5k


finished_nodes = []
results = {}
sleeping_times_nodes = {}

os.makedirs("experiment_logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logging.basicConfig(filename=f"experiment_logs/experiment_logs_{timestamp}.txt", format='%(asctime)s %(message)s', filemode="a+")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def execute_reconf_in_g5k(roles, version_concerto_name, assembly_name, reconf_config_file_path, duration, dep_num, node_num, experiment_num):
    timestamp_log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Execute reconf
    sleeping_times_nodes[assembly_name]["total_sleeping_time"] += time.time() - sleeping_times_nodes[assembly_name]["current_down_time"]
    concerto_d_g5k.execute_reconf(roles[assembly_name], version_concerto_name, reconf_config_file_path, duration, timestamp_log_dir, dep_num, experiment_num)
    sleeping_times_nodes[assembly_name]["current_down_time"] = time.time()

    # Fetch and compute results
    concerto_d_g5k.fetch_times_log_file(roles[assembly_name], assembly_name, dep_num, timestamp_log_dir)
    compute_results(assembly_name, concerto_d_g5k.build_times_log_path(assembly_name, dep_num, timestamp_log_dir))

    # Finish reconf for assembly name if its over
    # concerto_d_g5k.fetch_finished_reconfiguration_file(roles[assembly_name], version_concerto_name, assembly_name, dep_num)
    if exists(f"/home/anomond/{version_concerto_name}/concerto/{concerto_d_g5k.build_finished_reconfiguration_path(assembly_name, dep_num)}"):
        finished_nodes.append(node_num)


def compute_results(assembly_name: str, timestamp_log_file: str):
    with open(f"/home/anomond/evaluation/experiment/results_experiment/logs_files_assemblies/{timestamp_log_file}", "r") as f:
        loaded_results = yaml.safe_load(f)

    if assembly_name not in results.keys():
        results[assembly_name] = {
            "total_uptime_duration": 0,
            "total_loading_state_duration": 0,
            "total_deploy_duration": 0,
            "total_update_duration": 0,
            "total_saving_state_duration": 0
        }

    results[assembly_name]["total_uptime_duration"] += loaded_results["sleep_time"] - loaded_results["up_time"]
    results[assembly_name]["total_loading_state_duration"] += loaded_results["end_loading_state"] - loaded_results["start_loading_state"]
    if "end_saving_state" in loaded_results.keys() and "start_saving_state" in loaded_results.keys():
        results[assembly_name]["total_saving_state_duration"] += loaded_results["end_saving_state"] - loaded_results["start_saving_state"]
    if "start_deploy" in loaded_results.keys() and "end_deploy" in loaded_results.keys():
        results[assembly_name]["total_deploy_duration"] += loaded_results["end_deploy"] - loaded_results["start_deploy"]
    if "start_update" in loaded_results.keys() and "end_update" in loaded_results.keys():
        results[assembly_name]["total_update_duration"] += loaded_results["end_update"] - loaded_results["start_update"]


def find_next_uptime(uptimes_nodes):
    min_uptime = (0, (math.inf, math.inf))
    for node_num, uptimes_values in enumerate(uptimes_nodes):
        for uptime in uptimes_values:
            if uptime[0] < min_uptime[1][0]:
                min_uptime = (node_num, uptime)

    return min_uptime


def schedule_and_run_uptimes_from_config(roles, version_concerto_name, uptimes_nodes_tuples: List, reconfig_config_file_path, experiment_num):
    """
    TODO: Faire une liste ordonnée globale pour tous les assemblies, puis attendre (enlever les calculs
    qui prennent un peu de temps)
    TODO: à changer ? loader un json via yaml.load
    """
    log.debug("SCHEDULING START")
    expe_time_start = time.time()
    uptimes_nodes = [list(uptimes) for uptimes in uptimes_nodes_tuples]
    all_threads = []

    log.debug("UPTIMES TO TREAT")
    for node_num, uptimes in enumerate(uptimes_nodes):
        log.debug(f"node_num: {node_num}, uptimes: {uptimes}")
    finished_nodes.clear()

    while any(len(uptimes) > 0 for uptimes in uptimes_nodes):

        # Find the next reconf to launch (closest in time)
        node_num, next_uptime = find_next_uptime(uptimes_nodes)
        if node_num in finished_nodes:
            log.debug(f"{node_num} finished its reconfiguration, clearing all subsequent uptimes")
            uptimes_nodes[node_num].clear()
        elif next_uptime[0] <= time.time() - expe_time_start:

            # Init the thread that will handle the reconf
            duration = next_uptime[1]
            dep_num = None if node_num == 0 else node_num - 1
            assembly_name = "server" if node_num == 0 else f"dep{node_num - 1}"
            thread = Thread(target=execute_reconf_in_g5k, args=(roles, version_concerto_name, assembly_name, reconfig_config_file_path, duration, dep_num, node_num, experiment_num))

            # Start reconf and remove it from uptimes
            thread.start()
            all_threads.append(thread)
            uptimes_nodes[node_num].remove(next_uptime)
        else:
            # Wait until its time to launch the reconf
            n = (expe_time_start + next_uptime[0]) - time.time()
            log.debug(f"sleeping {n} seconds")
            time.sleep(n)

    # Wait for non finished threads
    for th in all_threads:
        th.join()

    log.debug("ALL UPTIMES HAVE BEEN PROCESSED")


def compute_end_reconfiguration_time(uptimes_nodes):
    max_uptime_value = 0
    for uptimes_node in uptimes_nodes:
        for uptime in uptimes_node:
            if uptime[0] + uptime[1] > max_uptime_value:
                max_uptime_value = uptime[0] + uptime[1]

    return max_uptime_value


def launch_experiment(is_normal, version_concerto_name, uptimes_file_name, transitions_times_file_name, cluster, experiment_num):
    # Provision infrastructure
    log.debug("------ Fetching infrastructure --------")
    with open(uptimes_file_name) as f:
        uptimes_nodes = json.load(f)

    # TODO: Need to do the reservation previsouly but still to precise roles and stuff, to change
    suffix = "-test" if not is_normal else ""
    roles, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(f"concerto-d{suffix}", nb_concerto_d_nodes=len(uptimes_nodes), nb_zenoh_routers=1, cluster=cluster)
    log.debug(roles, networks)

    # Create transitions time file
    # TODO: Mettre synchrone/asynchrone/Muse
    # TODO: Mettre les deux expériences (cf présentation) (donc ce qui est mesuré dans les deux expériences)
    # TODO: générer les fichiers en amont et uniquement passer leurs chemin au ParamSweeper

    # Reinitialize finished configuration states
    reinitialize_finished_config_state(uptimes_nodes, version_concerto_name)

    # Deploy zenoh routers
    if version_concerto_name == "concerto-decentralized":
        log.debug("------- Deploy zenoh routers -------")
        max_uptime_value = compute_end_reconfiguration_time(uptimes_nodes)
        concerto_d_g5k.install_zenoh_router(roles["zenoh_routers"])
        concerto_d_g5k.execute_zenoh_routers(roles["zenoh_routers"], max_uptime_value)

    # Reset results logs
    for assembly_name in results.keys():
        results[assembly_name] = {
            "total_uptime_duration": 0,
            "total_loading_state_duration": 0,
            "total_deploy_duration": 0,
            "total_update_duration": 0,
            "total_saving_state_duration": 0
        }

    # Run experiment
    log.debug("------- Run experiment ----------")
    nodes_names = ["server"] + [f"dep{i}" for i in range(len(uptimes_nodes) - 1)]
    for name in nodes_names:
        sleeping_times_nodes[name] = {
            "total_sleeping_time": 0,
            "current_down_time": time.time(),
        }

    schedule_and_run_uptimes_from_config(roles, version_concerto_name, uptimes_nodes, transitions_times_file_name, experiment_num)

    for name in nodes_names:
        results[name]["total_sleeping_time"] = sleeping_times_nodes[name]["total_sleeping_time"]

    # Save results
    save_results(version_concerto_name, cluster, transitions_times_file_name, uptimes_file_name, experiment_num)

    log.debug("------ End of experiment ---------")


def save_results(version_concerto_name, cluster, transitions_times_file_name, uptimes_file_name, expe_num):
    # Dans le nom: timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs("/home/anomond/results", exist_ok=True)
    full_path = f"/home/anomond/results/results_{timestamp}"
    log.debug(f"Saving results in {full_path}")
    with open(full_path, "w") as f:
        results_to_dump = {
            "parameters": {
                "version_concerto_name": version_concerto_name,
                "transitions_times_file_name": transitions_times_file_name,
                "uptimes_file_name": uptimes_file_name,
                "expe_num": expe_num,
                "cluster": cluster,
            },
            "results": results
        }
        json.dump(results_to_dump, f, indent=4)

    # Save config expe + results
    shutil.copytree(f"/home/anomond/{version_concerto_name}/concerto/finished_reconfigurations", f"/home/anomond/results/finished_reconfigurations_{timestamp}")


def reinitialize_finished_config_state(version_concerto_name, uptimes_nodes):
    log.debug("------- Removing previous finished_configurations files -------")
    path_server = f"/home/anomond/{version_concerto_name}/concerto/finished_reconfigurations/server_assembly"
    if exists(path_server):
        log.debug(f"Removing {path_server}")
        os.remove(path_server)
    for i in range(len(uptimes_nodes) - 1):
        path_dep = f"/home/anomond/{version_concerto_name}/concerto/finished_reconfigurations/dep_assembly_{i}"
        if exists(path_dep):
            log.debug(f"Removing {path_dep}")
            os.remove(path_dep)


def get_normal_parameters():
    uptimes_to_test = [
        "/home/anomond/parameters/uptimes/uptimes-30-30-12-0_02-0_05.json",
        "/home/anomond/parameters/uptimes/uptimes-30-30-12-0_2-0_3.json",
        "/home/anomond/parameters/uptimes/uptimes-30-30-12-0_5-0_6.json",
    ]

    transitions_times_list = [
        "/home/anomond/parameters/transitions_times/transitions_times-1-30-deps12-0.json",
        "/home/anomond/parameters/transitions_times/transitions_times-1-30-deps12-1.json"
    ]

    return uptimes_to_test, transitions_times_list


def get_test_parameters():
    uptimes_to_test = [
        "/home/anomond/parameters/uptimes/uptimes-30-30-2-0_98-1.json"
    ]

    transitions_times_list = [
        "/home/anomond/parameters/transitions_times/mock_transitions_times-1-30-deps2.json"
    ]

    return uptimes_to_test, transitions_times_list


def create_and_run_sweeper(is_normal, uptimes_to_test, transitions_times_list):
    version_concerto_name = "concerto-decentralized-synchrone"

    sweeps = sweep({
        "uptimes": uptimes_to_test,
        "transitions_times": transitions_times_list,
        "cluster": ["uvb"],
        "experiment_num": [1]
    })
    log.debug("--- All experiments to treat: ---")
    for k in sweeps:
        log.debug(k)
    log.debug("----------------------------------")
    suffix = "_test" if not is_normal else ""
    sweeper = ParamSweeper(
        persistence_dir=str(Path(f"experiment/sweeps{suffix}").resolve()), sweeps=sweeps, save_sweeps=True
    )
    parameter = sweeper.get_next()
    while parameter:
        try:
            log.debug("----- Launching experiment ---------")
            launch_experiment(is_normal, version_concerto_name, parameter["uptimes"], parameter["transitions_times"], parameter["cluster"], parameter["experiment_num"])
            sweeper.done(parameter)
        except Exception as e:
            sweeper.skip(parameter)
            log.debug("Experiment FAILED")
            log.exception(e)
            log.debug(e)
            log.debug(f"Skipping experiment with parameters {parameter}")
            traceback.print_exc()
        finally:
            parameter = sweeper.get_next()


if __name__ == '__main__':
    is_normal = len(sys.argv) > 1 and sys.argv[1] == "normal"
    if is_normal:
        uptimes_to_test, transitions_times_list = get_normal_parameters()
    else:
        uptimes_to_test, transitions_times_list = get_test_parameters()
    create_and_run_sweeper(is_normal, uptimes_to_test, transitions_times_list)
