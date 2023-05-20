import os
import shutil
from os.path import exists
from typing import Dict, List

import yaml

from experiment import globals_variables, metric_experiment_functions, log_experiment

home_dir = f"{os.getenv('HOME')}/concerto-d-projects"
target_dir = f"{os.getenv('HOME')}/experiments_results"


def save_expe_metadata(
        finished_reconfs_by_reconf_name,
        version_concerto_d,
        transitions_times,
        uptimes,
        waiting_rate,
        cluster
):
    # TODO: fix algo not correct
    finished_reconf = (
            all(res["finished_reconfiguration"] for res in finished_reconfs_by_reconf_name["deploy"].values())
            and all(res["finished_reconfiguration"] for res in finished_reconfs_by_reconf_name["update"].values())
    )

    # Save expe metadata
    metadata_expe = {
        "expe_parameters": {
            "version_concerto_name": version_concerto_d,
            "transitions_times_file_name": transitions_times,
            "uptimes_file_name": uptimes,
            "waiting_rate": waiting_rate,
            "cluster": cluster,
        },
        "expe_details": {
            "global_finished_reconf": finished_reconf,
            "details": finished_reconfs_by_reconf_name
        }
    }
    with open(f"{globals_variables.current_expe_dir}/execution_metadata.yaml", "w") as f:
        yaml.safe_dump(metadata_expe, f, sort_keys=False)


def compute_results_from_dir(expe_name, expe_dir_path: str, execution_dir: str, assemblies_names: List[str]):
    # Read metadata file and put it in results
    metadata_file_path = f"{expe_dir_path}/{execution_dir}/execution_metadata.yaml"
    log = log_experiment.log
    log.debug(f"Metadata file path: {metadata_file_path}")

    # If execution metadata file doesn't exists, it means the execution has been aborted, so don't compute the results
    if exists(metadata_file_path):
        results = {}
        with open(metadata_file_path) as f:
            loaded_metadata = yaml.safe_load(f)

        # Create a dict results with all assemblies names
        details_assemblies_results = {
            assembly_name: {"deploy": {}, "update": {}} for assembly_name in assemblies_names
        }

        version_concerto_d = loaded_metadata["expe_parameters"]["version_concerto_name"]
        # For each reconfiguration name
        for reconfiguration_name in ["deploy", "update"]:
            # Call compute_execution_metrics for total of each metric
            _compute_execution_metrics(f"{expe_dir_path}/{execution_dir}", version_concerto_d, reconfiguration_name, details_assemblies_results)

        # Sort by descending order (highest values on top)
        if "server-clients" in details_assemblies_results.keys():
            del details_assemblies_results["server-clients"]
        sorted_details_assemblies_results = {}
        for assembly_name, reconf_dicts in details_assemblies_results.items():
            sorted_details_assemblies_results[assembly_name] = reconf_dicts
            for reconf_name, values in reconf_dicts.items():
                sorted_details_assemblies_results[assembly_name][reconf_name] = {
                    timestamp_name: timestamp_value
                    for timestamp_name, timestamp_value in sorted(values.items(), key=lambda e: e[1], reverse=True)
                }

        # Compute metric of interest
        if loaded_metadata["expe_parameters"]["version_concerto_name"] == "central":
            global_results = _compute_global_results_central(sorted_details_assemblies_results)
        else:
            global_results = _compute_global_results(sorted_details_assemblies_results)
        global_results["global_finished_reconf"] = loaded_metadata["expe_details"]["global_finished_reconf"]
        if loaded_metadata["expe_parameters"]["version_concerto_name"] == "synchronous":
            global_synchronization_results = _compute_global_synchronization_results(sorted_details_assemblies_results)
        else:
            global_synchronization_results = {}

        results["expe_parameters"] = loaded_metadata["expe_parameters"]
        results["global_results"] = global_results
        if loaded_metadata["expe_parameters"]["version_concerto_name"] == "synchronous":
            results["global_synchronization_results"] = global_synchronization_results
        results["details_assemblies_results"] = sorted_details_assemblies_results
        results["expe_details"] = loaded_metadata["expe_details"]

        target_expe_dir = f"{target_dir}/{expe_name}"
        os.makedirs(target_expe_dir, exist_ok=True)
        shutil.copytree(f"{expe_dir_path}/{execution_dir}", f"{target_expe_dir}/{execution_dir}")
        target_file = f"{target_expe_dir}/{execution_dir}.yaml"

        # Save computed results
        print(f"Save computed results here: {target_file}")
        with open(target_file, "w") as f:
            yaml.dump(results, f, sort_keys=False)

        # Save also in execution dir
        print(f"Also save computed results here: {execution_dir}/{target_file}")
        with open(f"{target_expe_dir}/{execution_dir}/{execution_dir}.yaml", "w") as f:
            yaml.dump(results, f, sort_keys=False)

    else:
        results = {}
        print(f"Metadata file doesn't exist for {execution_dir}, result not computed")

    return results


# def compute_from_expe_dir(expe_dir: str, assemblies_names: List[str]):
#     expe_dir_path = f"{home_dir}/{expe_dir}"
#
#     # For each sub-dirs except experiment_logs and sweeps
#     for execution_dir in [dir_name for dir_name in os.listdir(expe_dir_path) if dir_name not in ["experiment_logs", "sweeps"]]:
#         compute_results_from_dir(expe_dir_path, execution_dir, assemblies_names)


def _compute_execution_metrics(current_dir: str, version_concerto_d: str, reconfiguration_name: str, details_assemblies_results: Dict):
    """
    Fill the param details_assemblies_results with metrics for the given reconfiguration name
    """
    logs_files_assemblies_dir = f"{current_dir}/logs_files_assemblies/{reconfiguration_name}"
    for file_name in os.listdir(logs_files_assemblies_dir):
        with open(f"{logs_files_assemblies_dir}/{file_name}") as f:
            loaded_results = yaml.safe_load(f)
        assembly_name = file_name.split("_")[0]
        if assembly_name not in details_assemblies_results:
            details_assemblies_results[assembly_name] = {"deploy": {}, "update": {}}

        if "mjuz" not in version_concerto_d or assembly_name == "server":
            for timestamp_name, timestamp_values in loaded_results.items():
                timestamp_name_to_save = f"total_{timestamp_name}_duration"
                if timestamp_name_to_save not in details_assemblies_results[assembly_name][reconfiguration_name]:
                    details_assemblies_results[assembly_name][reconfiguration_name][timestamp_name_to_save] = 0
                details_assemblies_results[assembly_name][reconfiguration_name][timestamp_name_to_save] += timestamp_values["end"] - timestamp_values["start"]


def build_save_results_name(expe_name, version_concerto_name, transitions_times_file_name, uptimes_file_name, waiting_rate, timestamp_name, cluster_name):
    file_name = "results_"
    file_name += expe_name
    file_name += f"_{version_concerto_name}"
    file_name += f"_{cluster_name}"

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
    if "0_02-0_02" in uptimes_file_name:
        file_name += "_perc-2-2"
    if "0_25-0_25" in uptimes_file_name:
        file_name += "_perc-25-35"
    if "0_5-0_5" in uptimes_file_name:
        file_name += "_perc-50-50"

    file_name += f"_waiting_rate-{waiting_rate}-{timestamp_name}"

    return file_name


def _compute_max_value_from_func(details_assemblies_results, compute_func):
    max_assembly_name, max_assembly_value = "", 0
    for assembly_name, assembly_reconfs_values in details_assemblies_results.items():
        assembly_value = compute_func(assembly_reconfs_values)
        if compute_func(assembly_reconfs_values) > max_assembly_value:
            max_assembly_name = assembly_name
            max_assembly_value = assembly_value

    return round(max_assembly_value, 2)


def _compute_global_results(details_assemblies_results):
    return {
        "max_deploy_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_deploy_duration_func),
        "max_update_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_update_duration_func),
        "max_reconf_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_reconf_duration_func),
        "max_sleeping_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_sleeping_duration_func),
        "max_execution_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_execution_duration_func),
    }


def _compute_global_results_central(details_assemblies_results):
    return {
        "max_deploy_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_deploy_duration_func_central),
        "max_update_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_update_duration_func_central),
        "max_reconf_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_reconf_duration_func_central),
        "max_sleeping_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_sleeping_duration_func),
        "max_execution_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_execution_duration_func),
    }


def _compute_global_synchronization_results(details_assemblies_results):
    return {
        "max_deploy_sync_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_deploy_sync_duration_func),
        "max_update_sync_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_update_sync_duration_func),
        "max_reconf_sync_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_reconf_sync_duration_func),
        "max_sleeping_sync_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_sleeping_sync_duration_func),
        "max_execution_sync_time": _compute_max_value_from_func(details_assemblies_results, metric_experiment_functions.max_execution_sync_duration_func),
    }


if __name__ == '__main__':
    expe_name = "expe_name"
    expe_dir_path = f"{home_dir}/experiment-test-central-correct-dir"
    compute_results_from_dir(
        expe_name,
        expe_dir_path, "results_central_T0_perc-50-60_waiting_rate-1-2023-01-03_17-47-53",
        ["server", "dep0", "dep1", "dep2", "dep3", "dep4", "dep5", "dep6", "dep7", "dep8", "dep9", "dep10", "dep11"]
    )
