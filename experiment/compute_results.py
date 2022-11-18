import os
import sys
from os.path import exists
from typing import Dict

import yaml

home_dir = f"{os.getenv('HOME')}/concerto-d-projects"
target_dir = f"{os.getenv('HOME')}/experiments_results"


def compute_from_expe_dir(expe_dir: str, nb_concerto_nodes: int = 12):
    expe_dir_path = f"{home_dir}/{expe_dir}"

    # For each sub-dirs except experiment_logs and sweeps
    for execution_dir in [dir_name for dir_name in os.listdir(expe_dir_path) if dir_name not in ["experiment_logs", "sweeps"]]:
        # Read metadata file and put it in results
        metadata_file_path = f"{expe_dir_path}/{execution_dir}/execution_metadata.yaml"

        # If execution metadata file doesn't exists, it means the execution has been aborted, so don't compute the results
        if exists(metadata_file_path):
            results = {}
            with open(metadata_file_path) as f:
                loaded_metadata = yaml.safe_load(f)

            # Create a dict results with all assemblies names
            details_assemblies_results = {
                assembly_name: {"deploy": {}, "update": {}} for assembly_name in
                # ["server", *[f"dep{i}" for i in range(nb_concerto_nodes)]]
                ["server"]
            }

            # For each reconfiguration name
            # for reconfiguration_name in ["deploy", "update"]:
            for reconfiguration_name in ["deploy"]:
                # Call compute_execution_metrics for total of each metric
                _compute_execution_metrics(f"{expe_dir_path}/{execution_dir}", reconfiguration_name, details_assemblies_results)

            # Sort by descending order (highest values on top)
            sorted_details_assemblies_results = {}
            for assembly_name, reconf_dicts in details_assemblies_results.items():
                sorted_details_assemblies_results[assembly_name] = reconf_dicts
                for reconf_name, values in reconf_dicts.items():
                    sorted_details_assemblies_results[assembly_name][reconf_name] = {timestamp_name: timestamp_value for timestamp_name, timestamp_value in sorted(values.items(), key=lambda e: e[1], reverse=True)}

            # Compute metric of interest
            global_results = _compute_global_results(sorted_details_assemblies_results)
            global_results["global_finished_reconf"] = loaded_metadata["expe_details"]["global_finished_reconf"]
            if loaded_metadata["expe_parameters"]["version_concerto_name"] == "synchronous":
                global_synchronization_results = _compute_global_synchronization_results(sorted_details_assemblies_results)
            else:
                global_synchronization_results = {}

            # Save file in target directory
            experiment_results_file_name = _build_save_results_file_name(
                loaded_metadata["expe_parameters"]["version_concerto_name"],
                loaded_metadata["expe_parameters"]["transitions_times_file_name"],
                loaded_metadata["expe_parameters"]["uptimes_file_name"],
                loaded_metadata["expe_parameters"]["waiting_rate"],
                execution_dir
            )

            results["expe_parameters"] = loaded_metadata["expe_parameters"]
            results["global_results"] = global_results
            if loaded_metadata["expe_parameters"]["version_concerto_name"] == "synchronous":
                results["global_synchronization_results"] = global_synchronization_results
            results["details_assemblies_results"] = sorted_details_assemblies_results
            results["expe_details"] = loaded_metadata["expe_details"]

            os.makedirs(target_dir, exist_ok=True)
            target_file = f"{target_dir}/{experiment_results_file_name}"
            print(f"Save computed results here: {target_file}")
            with open(target_file, "w") as f:
                yaml.dump(results, f, sort_keys=False)

        else:
            print(f"Metadata file doesn't exist for {execution_dir}, result not computed")


def _compute_execution_metrics(current_dir: str, reconfiguration_name: str, details_assemblies_results: Dict):
    """
    Fill the param details_assemblies_results with metrics for the given reconfiguration name
    """
    logs_files_assemblies_dir = f"{current_dir}/logs_files_assemblies/{reconfiguration_name}"
    for file_name in os.listdir(logs_files_assemblies_dir):
        with open(f"{logs_files_assemblies_dir}/{file_name}") as f:
            loaded_results = yaml.safe_load(f)
        assembly_name = file_name.split("_")[0]

        for timestamp_name, timestamp_values in loaded_results.items():
            timestamp_name_to_save = f"total_{timestamp_name}_duration"
            if timestamp_name_to_save not in details_assemblies_results[assembly_name][reconfiguration_name]:
                details_assemblies_results[assembly_name][reconfiguration_name][timestamp_name_to_save] = 0
            details_assemblies_results[assembly_name][reconfiguration_name][timestamp_name_to_save] += timestamp_values["end"] - timestamp_values["start"]


def _build_save_results_file_name(version_concerto_name, transitions_times_file_name, uptimes_file_name, waiting_rate, execution_dir):
    file_name = "results"
    file_name += "_synchronous" if version_concerto_name == "synchronous" else "_asynchronous"

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

    file_name += f"_waiting_rate-{waiting_rate}-{execution_dir}.yaml"

    return file_name


def _compute_global_results(details_assemblies_results):
    global_results = {}
    max_deploy_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"]["total_event_deploy_duration"])
    max_deploy_time = max_deploy_values["deploy"]["total_event_deploy_duration"]

    # max_update_values = max(details_assemblies_results.values(), key=lambda values: values["update"]["total_event_update_duration"])
    # max_update_time = max_update_values["update"]["total_event_update_duration"]

    # max_reconf_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"]["total_event_deploy_duration"] + values["update"]["total_event_update_duration"])
    # max_reconf_time = max_reconf_values["deploy"]["total_event_deploy_duration"] + max_reconf_values["update"]["total_event_update_duration"]

    # max_sleeping_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"]["total_event_sleeping_duration"] + values["update"]["total_event_sleeping_duration"])
    # max_sleeping_time = max_sleeping_values["deploy"]["total_event_sleeping_duration"] + max_sleeping_values["update"]["total_event_sleeping_duration"]

    # max_execution_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"]["total_event_sleeping_duration"] + values["update"]["total_event_sleeping_duration"]
    #                                                                                    + values["deploy"]["total_event_uptime_duration"] + values["update"]["total_event_uptime_duration"])
    # max_execution_time = (max_execution_values["deploy"]["total_event_sleeping_duration"] + max_execution_values["update"]["total_event_sleeping_duration"]
    #                      + max_execution_values["deploy"]["total_event_uptime_duration"] + max_execution_values["update"]["total_event_uptime_duration"])

    global_results.update({
        "max_deploy_time": round(max_deploy_time, 2),
        # "max_update_time": round(max_update_time, 2),
        # "max_reconf_time": round(max_reconf_time, 2),
        # "max_sleeping_time": round(max_sleeping_time, 2),
        # "max_execution_time": round(max_execution_time, 2),
    })

    return global_results


def _compute_global_synchronization_results(details_assemblies_results):
    global_results = {}
    max_deploy_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"].get("total_instruction_waitall_27_duration", 0) + values["deploy"].get("total_instruction_waitall_5_duration", 0))
    max_deploy_sync_time = max_deploy_values["deploy"].get("total_instruction_waitall_27_duration", 0) + max_deploy_values["deploy"].get("total_instruction_waitall_5_duration", 0)

    max_update_values = max(details_assemblies_results.values(), key=lambda values: values["update"].get("total_instruction_waitall_4_duration", 0) + values["update"].get("total_instruction_waitall_3_duration", 0))
    max_update_sync_time = max_update_values["update"].get("total_instruction_waitall_4_duration", 0) + max_update_values["update"].get("total_instruction_waitall_3_duration", 0)

    max_reconf_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"].get("total_instruction_waitall_27_duration", 0) + values["deploy"].get("total_instruction_waitall_5_duration", 0)
                                                                                  + values["update"].get("total_instruction_waitall_4_duration", 0) + values["update"].get("total_instruction_waitall_3_duration", 0))
    max_reconf_sync_time = (max_reconf_values["deploy"].get("total_instruction_waitall_27_duration", 0) + max_reconf_values["deploy"].get("total_instruction_waitall_5_duration", 0)
                          + max_reconf_values["update"].get("total_instruction_waitall_4_duration", 0) + max_reconf_values["update"].get("total_instruction_waitall_3_duration", 0))

    max_sleeping_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + values["update"].get("total_event_sleeping_wait_all_duration", 0))
    max_sleeping_sync_time = max_sleeping_values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + max_sleeping_values["update"].get("total_event_sleeping_wait_all_duration", 0)

    max_execution_values = max(details_assemblies_results.values(), key=lambda values: values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + values["update"].get("total_event_sleeping_wait_all_duration", 0)
                                                                                       + values["deploy"].get("total_event_uptime_wait_all_duration", 0) + values["update"].get("total_event_uptime_wait_all_duration", 0))
    max_execution_sync_time = (max_execution_values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + max_execution_values["update"].get("total_event_sleeping_wait_all_duration", 0)
                             + max_execution_values["deploy"].get("total_event_uptime_wait_all_duration", 0) + max_execution_values["update"].get("total_event_uptime_wait_all_duration", 0))

    global_results.update({
        "max_deploy_sync_time": round(max_deploy_sync_time, 2),
        "max_update_sync_time": round(max_update_sync_time, 2),
        "max_reconf_sync_time": round(max_reconf_sync_time, 2),
        "max_sleeping_sync_time": round(max_sleeping_sync_time, 2),
        "max_execution_sync_time": round(max_execution_sync_time, 2),
    })

    return global_results


if __name__ == '__main__':
    compute_from_expe_dir("experiment-remote-validation-sync-50-60-dir")
