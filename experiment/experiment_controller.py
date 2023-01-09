import json
import math
import os
import time
import traceback
from concurrent import futures
from datetime import datetime
from pathlib import Path
from typing import List

import yaml
from execo_engine import sweep, ParamSweeper, HashableDict

from experiment import globals_variables, concerto_d_g5k, log_experiment, compute_results

results = {}
sleeping_times_nodes = {}
DEFAULT_EVENT_PRIORITY = 0


class EndOfExperimentException(BaseException):
    def __init__(self):
        super().__init__()


mjuz_server_finished = False


def _execute_node_reconf_in_g5k(
        roles,
        version_concerto_d,
        assembly_name,
        reconf_config_file_path,
        dep_num,
        node_num,
        waiting_rate,
        reconfiguration_name,
        uptimes_node,
        nb_concerto_nodes,
        execution_start_time,
        environment,
        start_round_reconf,
        uptimes_file_name
):
    logs_assemblies_file = f"{globals_variables.current_expe_dir}/logs_files_assemblies/{reconfiguration_name}"
    os.makedirs(logs_assemblies_file, exist_ok=True)
    finished_reconfiguration = False
    round_reconf = start_round_reconf
    exit_code = 0  # Init exit code to 0 for algo

    while not finished_reconfiguration and round_reconf < len(uptimes_node):
        # Find next uptime
        current_time = time.time() - execution_start_time
        sleeping_time, duration = _compute_sleeping_duration_uptime_duration(current_time, uptimes_node)
        log_experiment.log.debug(f"Controller {node_num} sleep for {sleeping_time}")

        key_sleep_time = "event_sleeping_wait_all" if exit_code == 5 else "event_sleeping"

        # Sleep until the uptime
        sleep_times = {}
        sleep_times[key_sleep_time] = {"start": time.time()}
        time.sleep(sleeping_time)  # Wait until next execution
        sleep_times[key_sleep_time]["end"] = time.time()

        # Save metrics
        with open(f"{logs_assemblies_file}/{assembly_name}_sleeping_times-{round_reconf}.yaml", "w") as f:
            yaml.dump(sleep_times, f)

        exit_code, finished_reconfiguration = execute_and_get_results(
            assembly_name, dep_num, duration, environment,
            nb_concerto_nodes, node_num,
            reconf_config_file_path, reconfiguration_name,
            roles, version_concerto_d, waiting_rate, uptimes_file_name, execution_start_time
        )

        round_reconf += 1

    return finished_reconfiguration, round_reconf, node_num


def execute_and_get_results(
        assembly_name, dep_num, duration, environment,
        nb_concerto_nodes, node_num, reconf_config_file_path, reconfiguration_name, roles,
        version_concerto_d, waiting_rate, uptimes_file_name, execution_start_time
):
    # Execute reconf
    timestamp_log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    transitions_times_file = f"{globals_variables.all_executions_dir}/experiment_files/parameters/transitions_times/{reconf_config_file_path}"
    uptimes_file_name_absolute = f"{globals_variables.all_executions_dir}/experiment_files/parameters/uptimes/{uptimes_file_name}"

    if "server-clients" in assembly_name:
        assembly_type = "server-clients"
    elif "dep" in assembly_name:
        assembly_type = "dep"
    else:
        assembly_type = "server"

    if version_concerto_d in ["synchronous", "asynchronous", "central"]:
        exit_code = concerto_d_g5k.execute_reconf(
            roles[assembly_name], version_concerto_d, transitions_times_file,
            duration, timestamp_log_dir, nb_concerto_nodes, dep_num, waiting_rate,
            reconfiguration_name, environment, assembly_type, uptimes_file_name_absolute, execution_start_time
        )
    else:
        exit_code = concerto_d_g5k.execute_mjuz_reconf(
            roles[assembly_name], version_concerto_d, transitions_times_file,
            duration, timestamp_log_dir, nb_concerto_nodes, dep_num,
            waiting_rate, reconfiguration_name, environment, assembly_type
        )

    log_experiment.log.debug(f"Exit code: {exit_code} for {assembly_name}")

    # TODO: à généraliser à synchronous et asynchronous
    concerto_d_g5k.fetch_debug_log_files(roles[assembly_name], assembly_name, dep_num, environment)

    # Throw exception if exit_code is unexpected
    if exit_code not in [0, 5, 50]:
        raise Exception(f"Unexpected exit code for the the role: {roles[assembly_name][0].address} ({assembly_type}{dep_num}): {exit_code}")

    # Finish reconf for assembly name if its over
    global mjuz_server_finished
    finished_reconfiguration = False
    if exit_code == 50 or (version_concerto_d in ["mjuz", "mjuz-2-comps"] and mjuz_server_finished):
        log_experiment.log.debug(f"Node {node_num} finished")
        finished_reconfiguration = True

        if node_num == 0 and version_concerto_d in ["mjuz", "mjuz-2-comps"]:
            mjuz_server_finished = True

    return exit_code, finished_reconfiguration


def _compute_sleeping_duration_uptime_duration(time_to_check, uptimes_node):
    for uptime_num, uptime_values in enumerate(uptimes_node):
        uptime, duration = uptime_values

        # Si le uptime est à 0 pile, on autorise une approximation à 0.1 (notamment le dernier thread qui doit attendre
        # que tous les autres threads soient créés)
        if time_to_check <= uptime + 0.1:
            return uptime + 0.1 - time_to_check, duration

        # if uptime < time_to_check < uptime + duration//2:
        #     return 0, uptime + duration//2 - time_to_check


def _schedule_and_run_uptimes_from_config(
        roles,
        version_concerto_d,
        uptimes_nodes: List,
        reconfig_config_file_path,
        waiting_rate,
        reconfiguration_name,
        nb_concerto_nodes,
        environment,
        start_round_reconf,
        execution_start_time,
        uptimes_file_name
):
    """
    Controller of the experiment, spawn a thread for each node that is present in the uptimes list. The thread
    simulate the awakening, the sleeping time and the reconfiguration of a node.
    """
    log = log_experiment.log
    log.debug("SCHEDULING START")

    with futures.ThreadPoolExecutor(max_workers=nb_concerto_nodes) as executor:
        futures_to_proceed = []
        finished_reconfs = {}
        global mjuz_server_finished
        mjuz_server_finished = False
        for node_num in range(nb_concerto_nodes):
            uptimes_node = uptimes_nodes[node_num]
            dep_num = None if node_num == 0 else node_num - 1
            assembly_name = "server" if node_num == 0 else f"dep{node_num - 1}"
            exec_future = executor.submit(
                _execute_node_reconf_in_g5k,
                roles,
                version_concerto_d,
                assembly_name,
                reconfig_config_file_path,
                dep_num,
                node_num,
                waiting_rate,
                reconfiguration_name,
                uptimes_node,
                nb_concerto_nodes - 1,
                execution_start_time,
                environment,
                start_round_reconf,
                uptimes_file_name
            )
            futures_to_proceed.append(exec_future)
        for future in futures.as_completed(futures_to_proceed):
            try:
                finished_reconf, rounds_reconf, future_node_num = future.result()
                future_assembly_name = "server" if future_node_num == 0 else f"dep{future_node_num - 1}"
                finished_reconfs[future_assembly_name] = {
                    "finished_reconfiguration": finished_reconf,
                    "rounds_reconf": rounds_reconf,
                }
            except Exception as e:
                exc = future.exception()
                log.error(exc)
                log.error(e)
                print(exc)
                # TODO: Cancel all the futures and reset the pulumi dirs, etc if Mjuz
                raise exc

    log.debug("ALL UPTIMES HAVE BEEN PROCESSED")
    return finished_reconfs


# def run_central_assembly_from_config(
#         roles_concerto_d,
#         version_concerto_d,
#         uptimes_nodes_list,
#         transitions_times_file_name,
#         waiting_rate,
#         reconfiguration_name,
#         nb_concerto_nodes,
#         environment,
#         start_round_reconf,
#         execution_start_time
# ):



def reset_environment(version_concerto_d: str, environment: str, roles_concerto_d, uptimes_nodes):
    log = log_experiment.log

    # If asynchronous, deploy zenoh router
    if version_concerto_d == "asynchronous":
        log.debug("------- Deploy zenoh routers -------")
        if environment in ["remote", "raspberry"]:
            concerto_d_g5k.install_zenoh_router(roles_concerto_d["zenoh_routers"], version_concerto_d, environment)
        max_uptime_value = _compute_end_reconfiguration_time(uptimes_nodes)
        concerto_d_g5k.execute_zenoh_routers(roles_concerto_d["zenoh_routers"], max_uptime_value, environment)

    # If Mjuz, clean the previous environment before running again
    if version_concerto_d in ["mjuz", "mjuz-2-comps"]:
        log.debug("-------- Clean previous environment -------")
        log.debug("Clean running mjuz processes and reset previous pulumi dir")
        concerto_d_g5k.clean_previous_mjuz_environment(roles_concerto_d, environment)


def _compute_end_reconfiguration_time(uptimes_nodes):
    max_uptime_value = 0
    for uptimes_node in uptimes_nodes:
        for uptime in uptimes_node:
            if uptime[0] + uptime[1] > max_uptime_value:
                max_uptime_value = uptime[0] + uptime[1]

    return max_uptime_value


def launch_experiment_with_params(
        expe_name,
        version_concerto_d,
        nb_concerto_nodes,
        uptimes_file_name,
        transitions_times_file_name,
        waiting_rate,
        environment,
        roles_concerto_d,
        id_run
):
    log = log_experiment.log

    with open(f"{globals_variables.all_expes_dir}/experiment_files/parameters/uptimes/{uptimes_file_name}") as f:
        uptimes_nodes = json.load(f)

    # Create current execution dir and log_debug dir
    current_execution_dir = globals_variables.current_execution_dir
    concerto_d_g5k.create_dir(roles_concerto_d["concerto_d"], current_execution_dir, environment)

    # Put inventory file on each node
    log.debug("Put inventory file on each")
    inventory_name = globals_variables.inventory_name
    concerto_d_g5k.put_file(roles_concerto_d["concerto_d"], inventory_name, f"{current_execution_dir}/{inventory_name}", environment)

    # Clean and restore environment from previous run
    reset_environment(
        version_concerto_d,
        environment,
        roles_concerto_d,
        uptimes_nodes
    )

    # Run experiment
    log.debug("------- Run experiment ----------")
    uptimes_nodes_list = [list(uptimes) for uptimes in uptimes_nodes]
    finished_reconfs_by_reconf_name = {}
    start_round_reconf = 0
    execution_start_time = time.time()
    for reconfiguration_name in ["deploy", "update"]:
        if version_concerto_d != "central":
            finished_reconfs = _schedule_and_run_uptimes_from_config(
                roles_concerto_d,
                version_concerto_d,
                uptimes_nodes_list,
                transitions_times_file_name,
                waiting_rate,
                reconfiguration_name,
                nb_concerto_nodes,
                environment,
                start_round_reconf,
                execution_start_time,
                uptimes_file_name
            )
        else:
            exit_code, finished_reconf = execute_and_get_results(
                "server-clients",
                None,
                _compute_end_reconfiguration_time(uptimes_nodes),
                environment,
                12,
                0,
                transitions_times_file_name,
                reconfiguration_name,
                roles_concerto_d,
                version_concerto_d,
                waiting_rate,
                uptimes_file_name,
                execution_start_time
            )
            finished_reconfs = {
                "server-clients": {
                    "finished_reconfiguration": finished_reconf,
                    "rounds_reconf": 0,
                }
            }
        log.debug(f"Fetching all timestamps log files for {reconfiguration_name}")
        dst_dir = f"{globals_variables.current_expe_dir}/logs_files_assemblies/{reconfiguration_name}"
        src_dir = f"{globals_variables.current_execution_dir}/{reconfiguration_name}"
        roles_to_fetch = "server" if version_concerto_d in ["mjuz", "mjuz-2-comps"] else "concerto_d"
        concerto_d_g5k.fetch_dir(roles_concerto_d[roles_to_fetch], src_dir, dst_dir, environment)

        finished_reconfs_by_reconf_name[reconfiguration_name] = finished_reconfs
        start_round_reconf = max(finished_reconfs.values(), key=lambda ass_reconf: ass_reconf["rounds_reconf"])["rounds_reconf"]


    log.debug("------ End of experiment ---------")

    return finished_reconfs_by_reconf_name


def _parse_sweeper_parameters(params_to_sweep):
    """
    Helper function to have the choice of either do the cartesian product of all possible parameters
    combinations or to pass directly a list of specifics parameters to experiment
    """
    if type(params_to_sweep) == list:
        sweeps = [HashableDict(params) for params in params_to_sweep]
    else:
        sweeps = sweep(params_to_sweep)

    return sweeps


def create_param_sweeper(expe_name: str, sweeper_params):
    log = log_experiment.log
    experiment_results_dir = globals_variables.compute_current_expe_dir_from_name(expe_name)
    log.debug(f"Global expe dir: {experiment_results_dir}")
    sweeps = _parse_sweeper_parameters(sweeper_params)
    log.debug("------------------------ Execution of experiments start ------------------------")
    log.debug(f"Number of experiments: {len(sweeps)}")
    sweeper = ParamSweeper(
        persistence_dir=str(Path(f"{experiment_results_dir}/sweeps").resolve()), sweeps=sweeps, save_sweeps=True
    )

    # TODO: Reset inprogress (that haven't been tagged as skipped caused of crash), do not run this script concurrently
    # on the same sweeper
    sweeper.reset(reset_inprogress=True)
    sweeper = ParamSweeper(
        persistence_dir=str(Path(f"{experiment_results_dir}/sweeps").resolve()), sweeps=sweeps, save_sweeps=True
    )

    log.debug(sweeper)
    log.debug("----- All experiments parameters -----")
    log.debug(sweeper_params)
    log.debug("--------------------------------------")

    return sweeper
