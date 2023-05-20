import os
import sys
sys.path.append(f"{os.path.dirname(__file__)}/../../evaluation/experiment")

from experiment import execution_experiment


def check_and_print_diffs(expe_results, expe_expected_results):
    def print_val_in_red(val):
        if val >= 1 or val < 0:
            return '\033[91m' + str(val) + '\033[0m'  # See https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
        else:
            return str(val)

    # Assertions
    global_results = expe_results["global_results"]
    expected_global_results = expe_expected_results["global_results"]
    print()
    print("Global results")
    keys = ["max_deploy_time", "max_update_time", "max_reconf_time", "max_sleeping_time", "max_execution_time"]
    for key in keys:
        print(f"{key}: {global_results[key]} \\ {expected_global_results[key]}  delta: {print_val_in_red(round(global_results[key] - expected_global_results[key], 2))}")

    print()
    print("Global synchronization results")
    global_synchronization_results = expe_results["global_synchronization_results"]
    expected_global_synchronization_results = expe_expected_results["global_synchronization_results"]
    keys = ["max_deploy_sync_time", "max_update_sync_time", "max_reconf_sync_time", "max_sleeping_sync_time", "max_execution_sync_time"]
    for key in keys:
        print(f"{key}: {global_synchronization_results[key]} \\ {expected_global_synchronization_results[key]}  delta: {print_val_in_red(round(global_synchronization_results[key] - expected_global_synchronization_results[key], 2))}")


def execute_test(
    nb_dependencies,
    nb_servers,
    uptimes,
    transitions_times,
    version_concerto_d,
    expected_results_values,
    expected_synchronization_results_values,
):
    reservation_params = {
        "cluster": "local",
        "nb_dependencies": nb_dependencies,
        "nb_servers": nb_servers,
        "nb_server_clients": 0,
        "nb_provider_nodes": 0,
        "nb_chained_nodes": 0,
    }
    parameter = {
        "uptimes": uptimes,
        "transitions_times": transitions_times,
        "waiting_rate": 1,
        "id": 1
    }

    # Test 100% overlaps, parallels deps, 1 deps, 1 sec TT
    _, results = execution_experiment.execute_expe(
        environment="local",
        expe_name="test_fonctionnels",
        parameter=parameter,
        reservation_params=reservation_params,
        roles_concerto_d=roles_concerto_d,
        use_case_name="parallel_deps",
        version_concerto_d=version_concerto_d
    )

    (
        max_deploy_time,
        max_update_time,
        max_reconf_time,
        max_sleeping_time,
        max_execution_time
    ) = expected_results_values

    (
        max_deploy_sync_time,
        max_update_sync_time,
        max_reconf_sync_time,
        max_sleeping_sync_time,
        max_execution_sync_time
    ) = expected_synchronization_results_values

    expected_results = {
        "global_results": {
            "max_deploy_time": max_deploy_time,
            "max_update_time": max_update_time,
            "max_reconf_time": max_reconf_time,
            "max_sleeping_time": max_sleeping_time,
            "max_execution_time": max_execution_time,
        },
        "global_synchronization_results": {
            "max_deploy_sync_time": max_deploy_sync_time,
            "max_update_sync_time": max_update_sync_time,
            "max_reconf_sync_time": max_reconf_sync_time,
            "max_sleeping_sync_time": max_sleeping_sync_time,
            "max_execution_sync_time": max_execution_sync_time,
        }
    }

    check_and_print_diffs(results, expected_results)


if __name__ == "__main__":
    config_file_path = "tests_concerto_d/test_synchrone.yaml"
    (
        _,
        _,
        _,
        _,
        _,
        _,
        _,
        roles_concerto_d,
        _,
        _,
        _,
        _
    ) = execution_experiment.initialize_expe(config_file_path, testing=True)

    execute_test(
        nb_dependencies=1,
        nb_servers=1,
        uptimes="tests_fonctionnels/uptimes_tests_fonctionnels_100.json",
        transitions_times="tests_fonctionnels/transitions_times_test_fonctionnels_1_sec.json",
        version_concerto_d="synchronous",
        expected_results_values=[3, 4, 7, 0, 7],
        expected_synchronization_results_values=[1, 1, 2, 0, 2]
    )

    execute_test(
        nb_dependencies=3,
        nb_servers=1,
        uptimes="tests_fonctionnels/uptimes_tests_fonctionnels_100.json",
        transitions_times="tests_fonctionnels/transitions_times_test_fonctionnels_server_first.json",
        version_concerto_d="synchronous",
        expected_results_values=[10, 14.5, 24.5, 0, 24.5],
        expected_synchronization_results_values=[7, 10.5, 17.5, 0, 17.5]
    )
