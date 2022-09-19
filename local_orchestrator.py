import math
import subprocess
import time
from datetime import datetime
from os.path import exists
from threading import Thread

import yaml


def _find_next_uptime(uptimes_nodes):
    min_uptime = (0, (math.inf, math.inf))
    for node_num, uptimes_values in enumerate(uptimes_nodes):
        for uptime in uptimes_values:
            if uptime[0] < min_uptime[1][0]:
                min_uptime = (node_num, uptime)

    return min_uptime


finished_nodes = []


def _schedule_and_run_uptimes_from_config(
    uptimes_nodes_tuples,
    config_file_path,
    uptime_duration,
    waiting_rate,
    timestamp_log_dir,
    execution_expe_dir,
    version_concerto_d,
):
    """
    Controller of the experiment, spawn a thread for each node that is present in the uptimes list. The thread
    simulate the awakening, the sleeping time and the reconfiguration of a node.
    """
    print("SCHEDULING START")
    expe_time_start = time.time()
    uptimes_nodes = [list(uptimes) for uptimes in uptimes_nodes_tuples]
    all_threads = []

    print("UPTIMES TO TREAT")
    for node_num, uptimes in enumerate(uptimes_nodes):
        print(f"node_num: {node_num}, uptimes: {uptimes}")
    finished_nodes.clear()

    while any(len(uptimes) > 0 for uptimes in uptimes_nodes):

        # Find the next reconf to launch (closest in time)
        node_num, next_uptime = _find_next_uptime(uptimes_nodes)
        if node_num in finished_nodes:
            print(f"{node_num} finished its reconfiguration, clearing all subsequent uptimes")
            uptimes_nodes[node_num].clear()
        elif next_uptime[0] <= time.time() - expe_time_start:

            # Init the thread that will handle the reconf
            duration = next_uptime[1]
            dep_num = None if node_num == 0 else node_num - 1
            assembly_name = "server" if node_num == 0 else f"dep{node_num - 1}"
            thread = Thread(
                target=launch_reconfiguration,
                args=(
                    config_file_path,
                    uptime_duration,
                    waiting_rate,
                    timestamp_log_dir,
                    execution_expe_dir,
                    version_concerto_d,
                    node_num,
                    dep_num,
                )
            )

            # Start reconf and remove it from uptimes
            thread.start()
            all_threads.append(thread)
            uptimes_nodes[node_num].remove(next_uptime)
        else:
            # Wait until its time to launch the reconf
            n = (expe_time_start + next_uptime[0]) - time.time()
            print(f"sleeping {n} seconds")
            time.sleep(n)

    # Wait for non finished threads
    for th in all_threads:
        th.join()

    print("ALL UPTIMES HAVE BEEN PROCESSED")


def launch_reconfiguration(
        config_file_path,
        uptime_duration,
        waiting_rate,
        timestamp_log_dir,
        execution_expe_dir,
        version_concerto_d,
        node_num,
        dep_num
):
    command_args = []
    command_args.append("../concerto-decentralized/venv/bin/python3")               # Execute inside the python virtualenv
    assembly_name = "server" if dep_num is None else "dep"
    command_args.append(f"synthetic_use_case/reconf_programs/reconf_{assembly_name}.py")  # The reconf program to execute
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(str(uptime_duration))     # The awakening time of the program, it goes to sleep afterwards (it exits)
    command_args.append(str(waiting_rate))
    command_args.append(timestamp_log_dir)
    command_args.append(execution_expe_dir)
    command_args.append(version_concerto_d)
    if dep_num is not None:
        command_args.append(str(dep_num))

    env_process = {
        "PYTHONPATH": "$PYTHONPATH:.:./../concerto-decentralized"
    }
    process = subprocess.Popen(command_args, env=env_process)
    process.wait()

    file_name = f"{assembly_name}_assembly"
    if dep_num is not None: file_name += f"_{dep_num}"
    if exists(f"{timestamp}/finished_reconfigurations/{file_name}"):
        finished_nodes.append(node_num)


config_file_path = "../experiment_files/parameters/transitions_times/transitions_times-1-30-deps12-0.json"
uptimes_nodes_tuples_path = "../experiment_files/parameters/uptimes/uptimes-60-30-12-1-1-1.json"

with open(uptimes_nodes_tuples_path) as f:
    uptimes_nodes_tuples = yaml.safe_load(f)

timestamp = f"local_exec_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
_schedule_and_run_uptimes_from_config(
    uptimes_nodes_tuples,
    config_file_path,
    30,
    1,
    timestamp,
    timestamp,
    "synchronous"
)
