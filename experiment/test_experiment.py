import json
import time

from enoslib import Host

from experiment import globals_variables, log_experiment, experiment_controller, concerto_d_g5k


def test_fetch_times_log_file():
        globals_variables.local_execution_params_dir = "/home/aomond/concerto-d-projects"
        globals_variables.g5k_execution_params_dir = "/home/anomond/concerto-d-projects"
        globals_variables.initialize_remote_execution_expe_dir_name("test")
        log_experiment.initialize_logging("test-de-ouf-mock", mock=True)
        roles_nodes = {
                "server": [Host(address="econome-1.nantes.grid5000.fr")],
                "dep0": [Host(address="econome-10.nantes.grid5000.fr")],
                "dep1": [Host(address="econome-11.nantes.grid5000.fr")],
                "dep2": [Host(address="econome-12.nantes.grid5000.fr")],
                "dep3": [Host(address="econome-14.nantes.grid5000.fr")],
                "dep4": [Host(address="econome-20.nantes.grid5000.fr")],
                "dep5": [Host(address="econome-21.nantes.grid5000.fr")],
                "dep6": [Host(address="econome-22.nantes.grid5000.fr")],
                "dep7": [Host(address="econome-3.nantes.grid5000.fr")],
                "dep8": [Host(address="econome-4.nantes.grid5000.fr")],
                "dep9": [Host(address="econome-5.nantes.grid5000.fr")],
                "dep10": [Host(address="econome-6.nantes.grid5000.fr")],
                "dep11": [Host(address="econome-8.nantes.grid5000.fr")]
        }
        concerto_d_g5k.fetch_times_log_file(
                roles_nodes["server"],
                assembly_name="server",
                dep_num=None,
                timestamp_log_file="test",
                reconfiguration_name="deploy",
                environment="remote"
        )


def test_execute_reconf():
        globals_variables.initialize_remote_execution_expe_dir_name("test")
        # globals_variables.g5k_executions_expe_logs_dir = "/home/anomond/concerto-d-projects"
        # globals_variables.g5k_execution_params_dir = "/home/anomond/concerto-d-projects/execution-remote-test-failed-futures-test-subprocess-2022-10-20_13-23-53"
        concerto_d_g5k.execute_reconf(
                role_node=[Host(address="econome-1.nantes.grid5000.fr")],
                version_concerto_d="synchronous",
                config_file_path="/home/anomond/concerto-d-projects/experiment_files/parameters/transitions_times/transitions_times-1-30-deps12-1.json",
                duration=30,
                timestamp_log_file="2022-10-20_13-23-54",
                nb_concerto_nodes=12,
                dep_num=11,
                waiting_rate=1,
                reconfiguration_name="deploy",
                environment="remote"
        )


def test_execute_node_reconf_in_g5k():
        globals_variables.g5k_executions_expe_logs_dir = "/home/anomond/concerto-d-projects"
        globals_variables.g5k_execution_params_dir = "/home/anomond/concerto-d-projects/execution-remote-test-failed-futures-test-subprocess-2022-10-20_13-23-53"
        log_experiment.initialize_logging("test-de-ouf-mock", mock=True)
        roles_nodes = {
                "server": [Host(address="econome-1.nantes.grid5000.fr")],
                "dep0": [Host(address="econome-10.nantes.grid5000.fr")],
                "dep1": [Host(address="econome-11.nantes.grid5000.fr")],
                "dep2": [Host(address="econome-12.nantes.grid5000.fr")],
                "dep3": [Host(address="econome-14.nantes.grid5000.fr")],
                "dep4": [Host(address="econome-20.nantes.grid5000.fr")],
                "dep5": [Host(address="econome-21.nantes.grid5000.fr")],
                "dep6": [Host(address="econome-22.nantes.grid5000.fr")],
                "dep7": [Host(address="econome-3.nantes.grid5000.fr")],
                "dep8": [Host(address="econome-4.nantes.grid5000.fr")],
                "dep9": [Host(address="econome-5.nantes.grid5000.fr")],
                "dep10": [Host(address="econome-6.nantes.grid5000.fr")],
                "dep11": [Host(address="econome-8.nantes.grid5000.fr")]
        }
        with open(f"/home/aomond/concerto-d-projects/experiment_files/parameters/uptimes/uptimes-60-30-12-1-1-1.json") as f:
                uptimes_nodes = json.load(f)
        # uptimes_nodes_list = [list(uptimes) for uptimes in uptimes_nodes]
        uptimes_nodes_list = [[(0, 3)]]
        experiment_controller._execute_node_reconf_in_g5k(
                roles=roles_nodes,
                version_concerto_d="synchronous",
                assembly_name="server",
                reconf_config_file_path="transitions_times-1-30-deps12-1.json",
                dep_num=None,
                node_num=0,
                waiting_rate=1,
                reconfiguration_name="deploy",
                uptimes_node=uptimes_nodes_list[0],
                nb_concerto_nodes=12,
                execution_start_time=time.time(),
                environment="remote"
        )


# test_fetch_times_log_file()
# test_execute_reconf()
test_execute_node_reconf_in_g5k()