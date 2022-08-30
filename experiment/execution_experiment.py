import json
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

from experiment import globals_variables, concerto_d_g5k, log_experiment

finished_nodes = []
results = {}
sleeping_times_nodes = {}


def execute_reconf_in_g5k(roles, version_concerto_name, assembly_name, reconf_config_file_path, duration, dep_num, node_num, experiment_num, timeout):
    remote_execution_expe_dir = globals_variables.remote_execution_expe_dir
    timestamp_log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    transitions_times_file = f"{globals_variables.remote_homedir}/experiment_files/parameters/transitions_times/{reconf_config_file_path}"

    # Execute reconf
    sleeping_times_nodes[assembly_name]["total_sleeping_time"] += time.time() - sleeping_times_nodes[assembly_name]["current_down_time"]
    concerto_d_g5k.execute_reconf(roles[assembly_name], version_concerto_name, transitions_times_file, duration, timestamp_log_dir, dep_num, experiment_num, timeout)
    sleeping_times_nodes[assembly_name]["current_down_time"] = time.time()

    # Fetch and compute results
    concerto_d_g5k.fetch_times_log_file(roles[assembly_name], assembly_name, dep_num, timestamp_log_dir)
    compute_results(assembly_name, concerto_d_g5k.build_times_log_path(assembly_name, dep_num, timestamp_log_dir))

    # Finish reconf for assembly name if its over
    concerto_d_g5k.fetch_finished_reconfiguration_file(roles[assembly_name], assembly_name, dep_num)
    print(f"{globals_variables.local_execution_expe_dir}/{concerto_d_g5k.build_finished_reconfiguration_path(assembly_name, dep_num)}")
    print(exists(f"{globals_variables.local_execution_expe_dir}/{concerto_d_g5k.build_finished_reconfiguration_path(assembly_name, dep_num)}"))
    if exists(f"{globals_variables.local_execution_expe_dir}/{concerto_d_g5k.build_finished_reconfiguration_path(assembly_name, dep_num)}"):

        finished_nodes.append(node_num)


def compute_results(assembly_name: str, timestamp_log_file: str):
    with open(f"{globals_variables.local_execution_expe_dir}/logs_files_assemblies/{timestamp_log_file}") as f:
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


def schedule_and_run_uptimes_from_config(roles, version_concerto_name, uptimes_nodes_tuples: List, reconfig_config_file_path, experiment_num, timeout):
    log = log_experiment.log
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
            thread = Thread(target=execute_reconf_in_g5k, args=(roles, version_concerto_name, assembly_name, reconfig_config_file_path, duration, dep_num, node_num, experiment_num, timeout))

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


def launch_experiment(expe_name, job_name, nb_concerto_nodes, nb_zenoh_routers, version_concerto_name, uptimes_file_name, transitions_times_file_name, cluster, experiment_num, timeout):
    # TODO: enlever le paramètre roles
    log = log_experiment.log
    with open(f"{globals_variables.local_homedir}/experiment_files/parameters/uptimes/{uptimes_file_name}") as f:
        uptimes_nodes = json.load(f)

    log.debug("------ Fetching infrastructure --------")
    # Fetch reserved infrastructure
    # TODO: fetch from job_name instead of reserve
    # TODO: ne pas fetch depuis la longueur des uptimes nodes mais plutôt du nombre de nodes réservées à Concerto-D
    roles, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster)
    log.debug(roles, networks)

    # Initialize expe dirs and get uptimes nodes
    globals_variables.initialize_remote_execution_expe_dir_name(expe_name)
    os.makedirs(globals_variables.local_execution_expe_dir, exist_ok=True)
    concerto_d_g5k.initialize_remote_expe_dirs(roles["server"])

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
    nodes_names = ["server"] + [f"dep{i}" for i in range(len(uptimes_nodes) - 1)]
    for name in nodes_names:
        sleeping_times_nodes[name] = {
            "total_sleeping_time": 0,
            "current_down_time": time.time(),
        }

    # Run experiment
    log.debug("------- Run experiment ----------")
    schedule_and_run_uptimes_from_config(roles, version_concerto_name, uptimes_nodes, transitions_times_file_name, experiment_num, timeout)

    # Save results
    for name in nodes_names:
        results[name]["total_sleeping_time"] = sleeping_times_nodes[name]["total_sleeping_time"]
    save_results(version_concerto_name, cluster, transitions_times_file_name, uptimes_file_name, experiment_num, timeout)

    log.debug("------ End of experiment ---------")


def build_save_results_file_name(version_concerto_name, transitions_times_file_name, uptimes_file_name, expe_num, timeout):
    file_name = "results"
    file_name += "_synchrone" if "synchrone" in version_concerto_name else "_asynchrone"

    if "1-30-deps12-0" in transitions_times_file_name:
        file_name += "_T0"
    else:
        file_name += "_T1"

    if "1-1" in uptimes_file_name:
        file_name += "_perc-1-1"
    if "0_02-0_05" in uptimes_file_name:
        file_name += "_perc-2-5"
    if "0_2-0_3" in uptimes_file_name:
        file_name += "_perc-20-30"
    if "0_5-0_6" in uptimes_file_name:
        file_name += "_perc-50-60"

    file_name += f"_timeout-{timeout}"

    file_name += f"_expe_{expe_num}.json"

    return file_name


def save_results(version_concerto_name, cluster, transitions_times_file_name, uptimes_file_name, expe_num, timeout):
    log = log_experiment.log
    dir_to_save_expe = globals_variables.local_execution_expe_dir
    # Dans le nom: timestamp
    log.debug(f"Saving results in dir {dir_to_save_expe}")

    # File name
    file_name = build_save_results_file_name(version_concerto_name, transitions_times_file_name, uptimes_file_name, expe_num, timeout)

    global_results = {}
    reconf_dir_path = f"{dir_to_save_expe}/finished_reconfigurations"
    if not exists(reconf_dir_path):
        global_results["finished_reconf"] = False
    else:
        global_results["finished_reconf"] = len(os.listdir(reconf_dir_path)) == 13  # 12 deps + 1 server
        for f in os.listdir(reconf_dir_path):
            name = f.replace("_", "").replace("assembly", "")
            results[name].update({"finished_reconf": True})

    max_deploy_values = max(results.values(), key=lambda values: values["total_deploy_duration"])
    max_deploy_time = max_deploy_values["total_deploy_duration"]

    max_update_values = max(results.values(), key=lambda values: values["total_update_duration"])
    max_update_time = max_update_values["total_update_duration"]

    max_reconf_time = max_deploy_time + max_update_time

    max_sleeping_values = max(results.values(), key=lambda values: values["total_sleeping_time"])
    max_sleeping_time = max_sleeping_values["total_sleeping_time"]

    max_execution_values = max(results.values(), key=lambda values: values["total_sleeping_time"] + values["total_uptime_duration"])
    max_execution_time = max_execution_values["total_sleeping_time"] + max_execution_values["total_uptime_duration"]

    global_results.update({
        "max_deploy_time": round(max_deploy_time, 2),
        "max_update_time": round(max_update_time, 2),
        "max_reconf_time": round(max_reconf_time, 2),
        "max_sleeping_time": round(max_sleeping_time, 2),
        "max_execution_time": round(max_execution_time, 2),
    })

    with open(f"{dir_to_save_expe}/{file_name}", "w") as f:
        results_to_dump = {
            "parameters": {
                "version_concerto_name": version_concerto_name,
                "transitions_times_file_name": transitions_times_file_name,
                "uptimes_file_name": uptimes_file_name,
                "expe_num": expe_num,
                "cluster": cluster,
            },
            "global_results": global_results,
            "results": results,
        }
        json.dump(results_to_dump, f, indent=4)

    # Save config expe + results
    if exists(f"{globals_variables.local_homedir}/{dir_to_save_expe}/finished_reconfigurations"):
        shutil.copytree(f"{globals_variables.local_homedir}/{dir_to_save_expe}/finished_reconfigurations", f"{dir_to_save_expe}/finished_reconfigurations_{file_name}")


# def reinitialize_reconf_files(version_concerto_name):
#     log.debug("------- Removing previous finished_configurations files -------")
#     shutil.rmtree(f"/home/anomond/{version_concerto_name}/concerto/finished_reconfigurations", ignore_errors=True)
#     shutil.rmtree(f"/home/anomond/{version_concerto_name}/concerto/communication_cache", ignore_errors=True)
#     shutil.rmtree(f"/home/anomond/{version_concerto_name}/concerto/reprise_configs", ignore_errors=True)


# def get_normal_parameters():
#     uptimes_to_test = [
#         "/home/anomond/parameters/uptimes/uptimes-60-30-12-0_5-0_6.json",
#         "/home/anomond/parameters/uptimes/uptimes-60-30-12-0_2-0_3.json",
#         "/home/anomond/parameters/uptimes/uptimes-60-30-12-0_02-0_05.json",
#         "/home/anomond/parameters/uptimes/uptimes-60-30-12-1-1-1.json",
#     ]
#
#     transitions_times_list = [
#         "/home/anomond/parameters/transitions_times/transitions_times-1-30-deps12-0.json",
#         "/home/anomond/parameters/transitions_times/transitions_times-1-30-deps12-1.json"
#     ]
#
#     return uptimes_to_test, transitions_times_list
#
#
# def get_test_parameters():
#     uptimes_to_test = [
#         "/home/anomond/parameters/uptimes/uptimes-60-30-12-0_2-0_3.json",
#     ]
#
#     transitions_times_list = [
#         "/home/anomond/parameters/transitions_times/transitions_times-1-30-deps12-0.json"
#     ]
#
#     return uptimes_to_test, transitions_times_list


def create_and_run_sweeper(expe_name, job_name, nb_concerto_nodes, nb_zenoh_routers, cluster, version_concerto_name, params_to_sweep, roles):
    log = log_experiment.log
    global_local_dir_expe = globals_variables.global_local_dir_expe(expe_name)
    log.debug(f"Global expe dir: {global_local_dir_expe}")
    sweeps = sweep(params_to_sweep)
    sweeper = ParamSweeper(
        persistence_dir=str(Path(f"{global_local_dir_expe}/sweeps").resolve()), sweeps=sweeps, save_sweeps=True
    )

    # Reset inprogress (that haven't been tagged as skipped caused of crash), do not run this script concurrently
    # on the same sweeper
    sweeper.reset(reset_inprogress=True)
    sweeper = ParamSweeper(
        persistence_dir=str(Path(f"{global_local_dir_expe}/sweeps").resolve()), sweeps=sweeps, save_sweeps=True
    )
    parameter = sweeper.get_next()
    while parameter:
        try:
            log.debug("----- Launching experiment ---------")
            launch_experiment(
                expe_name,
                job_name,
                nb_concerto_nodes,
                nb_zenoh_routers,
                version_concerto_name,
                parameter["uptimes"],
                parameter["transitions_times"],
                cluster,
                parameter["experiment_num"],
                parameter["timeout"]
            )
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


# if __name__ == '__main__':
#     job_name = sys.argv[1]
#     version_concerto_name = sys.argv[2]
#     # parameters_file = sys.argv[3]
#     if version_concerto_name == "concerto-decentralized":
#         parameters_files = [
#             "last_results_async_0.json",
#             "last_results_async_1.json",
#             "last_results_async_2.json",
#         ]
#         for parameters_file in parameters_files:
#             with open(f"{globals_variables.local_homedir}/parameters/{parameters_file}") as f:
#                 params_to_sweep = json.load(f)
#             create_and_run_sweeper(job_name, version_concerto_name, params_to_sweep )
#     else:
#         parameters_files = [
#             "last_results_sync_0.json",
#             "last_results_sync_1.json",
#             "last_results_sync_2.json",
#             "last_results_sync_3.json",
#         ]
#         for parameters_file in parameters_files:
#             with open(f"/home/anomond/parameters/{parameters_file}") as f:
#                 params_to_sweep = json.load(f)
#             create_and_run_sweeper(job_name, version_concerto_name, params_to_sweep )