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
        environment
):
    logs_assemblies_file = f"{globals_variables.local_execution_params_dir}/logs_files_assemblies/{reconfiguration_name}"
    os.makedirs(logs_assemblies_file, exist_ok=True)
    finished_reconfiguration = False
    round_reconf = 0
    exit_code = 0  # Init exit code to 0 for algo

    while not finished_reconfiguration and round_reconf < len(uptimes_node):
        # Find next uptime
        next_uptime, duration = uptimes_node[round_reconf]
        sleeping_time = abs(execution_start_time + next_uptime - time.time())
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

        # Execute reconf
        timestamp_log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        transitions_times_file = f"{globals_variables.g5k_executions_expe_logs_dir}/experiment_files/parameters/transitions_times/{reconf_config_file_path}"
        exit_code = concerto_d_g5k.execute_reconf(roles[assembly_name], version_concerto_d, transitions_times_file, duration, timestamp_log_dir, nb_concerto_nodes, dep_num, waiting_rate, reconfiguration_name, environment)

        # Fetch results
        concerto_d_g5k.fetch_times_log_file(roles[assembly_name], assembly_name, dep_num, timestamp_log_dir, reconfiguration_name, environment)
        print(f"got here with exit code {exit_code}")
        # Finish reconf for assembly name if its over
        if exit_code == 50:
            log_experiment.log.debug(f"Node {node_num} finished")
            finished_reconfiguration = True

        round_reconf += 1

    return finished_reconfiguration, round_reconf, node_num


def _compute_execution_metrics(assembly_name: str, timestamp_log_file: str, reconfiguration_name: str):
    with open(f"{globals_variables.local_execution_params_dir}/logs_files_assemblies/{reconfiguration_name}/{timestamp_log_file}") as f:
        loaded_results = yaml.safe_load(f)

    if assembly_name not in results.keys():
        results[assembly_name] = {}

    for timestamp_name, timestamp_values in loaded_results.items():
        timestamp_name_to_save = f"total_{timestamp_name}_duration"
        if timestamp_name_to_save not in results[assembly_name]:
            results[assembly_name][timestamp_name_to_save] = 0
        results[assembly_name][timestamp_name_to_save] += timestamp_values["end"] - timestamp_values["start"]  # TODO: magic values refacto


def _find_next_uptime(uptimes_nodes):
    min_uptime = (0, (math.inf, math.inf))
    for node_num, uptimes_values in enumerate(uptimes_nodes):
        for uptime in uptimes_values:
            if uptime[0] < min_uptime[1][0]:
                min_uptime = (node_num, uptime)

    return min_uptime


def _schedule_and_run_uptimes_from_config(
        roles,
        version_concerto_d,
        uptimes_nodes: List,
        reconfig_config_file_path,
        waiting_rate,
        reconfiguration_name,
        nb_concerto_nodes,
        environment
):
    """
    Controller of the experiment, spawn a thread for each node that is present in the uptimes list. The thread
    simulate the awakening, the sleeping time and the reconfiguration of a node.
    """
    log = log_experiment.log
    log.debug("SCHEDULING START")
    execution_start_time = time.time()

    with futures.ThreadPoolExecutor(max_workers=nb_concerto_nodes) as executor:
        futures_to_proceed = []
        finished_reconfs = {}
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
                environment
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
                log.error(future.exception())
                print("exception was raised for future")
                raise e

    log.debug("ALL UPTIMES HAVE BEEN PROCESSED")
    return finished_reconfs


def _compute_end_reconfiguration_time(uptimes_nodes):
    max_uptime_value = 0
    for uptimes_node in uptimes_nodes:
        for uptime in uptimes_node:
            if uptime[0] + uptime[1] > max_uptime_value:
                max_uptime_value = uptime[0] + uptime[1]

    return max_uptime_value


def _launch_experiment_with_params(
        expe_name,
        cluster,
        version_concerto_d,
        nb_concerto_nodes,
        uptimes_file_name,
        transitions_times_file_name,
        waiting_rate,
        environment,
        roles_concerto_d
):
    log = log_experiment.log
    with open(f"{globals_variables.all_experiments_results_dir}/experiment_files/parameters/uptimes/{uptimes_file_name}") as f:
        uptimes_nodes = json.load(f)

    # Initialize expe dirs and get uptimes nodes
    globals_variables.initialize_remote_execution_expe_dir_name(expe_name)
    os.makedirs(globals_variables.local_execution_params_dir, exist_ok=True)
    log.debug(f"------------ Local execution expe dir on {globals_variables.local_execution_params_dir} ---------------------")
    log.debug(f"------------ Remote execution expe dir on {globals_variables.g5k_execution_params_dir} ---------------------")

    # If asynchronous, deploy zenoh router
    if version_concerto_d == "asynchronous":
        log.debug("------- Deploy zenoh routers -------")
        if environment == "remote":
            concerto_d_g5k.install_zenoh_router(roles_concerto_d["zenoh_routers"])
        max_uptime_value = _compute_end_reconfiguration_time(uptimes_nodes)
        concerto_d_g5k.execute_zenoh_routers(roles_concerto_d["zenoh_routers"], max_uptime_value, environment)

    # Run experiment
    log.debug("------- Run experiment ----------")
    uptimes_nodes_list = [list(uptimes) for uptimes in uptimes_nodes]
    finished_reconfs_by_reconf_name = {}
    for reconfiguration_name in ["deploy", "update"]:
        finished_reconfs = _schedule_and_run_uptimes_from_config(
            roles_concerto_d,
            version_concerto_d,
            uptimes_nodes_list,
            transitions_times_file_name,
            waiting_rate,
            reconfiguration_name,
            nb_concerto_nodes,
            environment
        )
        finished_reconfs_by_reconf_name[reconfiguration_name] = finished_reconfs

    finished_reconf = (
            all(finished_reconfs_by_reconf_name["deploy"].values()) and
            all(finished_reconfs_by_reconf_name["update"].values())
    )

    # Save expe metadata
    metadata_expe = {
        "expe_parameters": {
            "version_concerto_name": version_concerto_d,
            "transitions_times_file_name": transitions_times_file_name,
            "uptimes_file_name": uptimes_file_name,
            "waiting_rate": waiting_rate,
            "cluster": cluster,
        },
        "expe_details": {
            "global_finished_reconf": finished_reconf,
            "details": finished_reconfs_by_reconf_name
        }
    }
    with open(f"{globals_variables.local_execution_params_dir}/execution_metadata.yaml", "w") as f:
        yaml.safe_dump(metadata_expe, f, sort_keys=False)

    compute_results.compute_from_expe_dir(f"experiment-{expe_name}-dir")

    log.debug("------ End of experiment ---------")


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


def create_and_run_sweeper(expe_name, cluster, version_concerto_d, nb_concerto_nodes, params_to_sweep, environment, roles_concerto_d):
    log = log_experiment.log
    experiment_results_dir = globals_variables.experiment_results_dir(expe_name)
    log.debug(f"Global expe dir: {experiment_results_dir}")
    sweeps = _parse_sweeper_parameters(params_to_sweep)
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
    parameter = sweeper.get_next()
    print(sweeper)
    while parameter:
        try:
            log.debug("----- Launching experiment ---------")
            _launch_experiment_with_params(
                expe_name,
                cluster,
                version_concerto_d,
                nb_concerto_nodes,
                parameter["uptimes"],
                parameter["transitions_times"],
                parameter["waiting_rate"],
                environment,
                roles_concerto_d
            )
            sweeper.done(parameter)
            log.debug(f"Parameter {parameter} done")
            log.debug(f"State of the sweeper: {sweeper}")
        except Exception as e:
            sweeper.skip(parameter)
            log.debug("Experiment FAILED")
            log.debug(e)
            log.debug(f"Skipping experiment with parameters {parameter}")
            traceback.print_exc()
        finally:
            parameter = sweeper.get_next()
