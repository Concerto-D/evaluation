def max_deploy_duration_func(assemblies_values):
    return assemblies_values["deploy"].get("total_event_deploy_duration", 0)


def max_update_duration_func(assemblies_values):
    return assemblies_values["update"].get("total_event_update_duration", 0)


def max_reconf_duration_func(assemblies_values):
    return assemblies_values["deploy"].get("total_event_deploy_duration", 0) + assemblies_values["update"].get("total_event_update_duration", 0)


def max_sleeping_duration_func(assemblies_values):
    return assemblies_values["deploy"].get("total_event_sleeping_duration", 0) + assemblies_values["update"].get("total_event_sleeping_duration", 0)


def max_execution_duration_func(assemblies_values):
    return (assemblies_values["deploy"].get("total_event_sleeping_duration", 0) + assemblies_values["update"].get("total_event_sleeping_duration", 0)
          + assemblies_values["deploy"].get("total_event_uptime_duration", 0) + assemblies_values["update"].get("total_event_uptime_duration", 0))


def max_deploy_sync_duration_func(assemblies_values):
    return assemblies_values["deploy"].get("total_instruction_waitall_27_duration", 0) + assemblies_values["deploy"].get("total_instruction_waitall_5_duration", 0)


def max_update_sync_duration_func(assemblies_values):
    return assemblies_values["update"].get("total_instruction_waitall_4_duration", 0) + assemblies_values["update"].get("total_instruction_waitall_3_duration", 0)


def max_reconf_sync_duration_func(assemblies_values):
    return (assemblies_values["deploy"].get("total_instruction_waitall_27_duration", 0) + assemblies_values["deploy"].get("total_instruction_waitall_5_duration", 0)
          + assemblies_values["update"].get("total_instruction_waitall_4_duration", 0) + assemblies_values["update"].get("total_instruction_waitall_3_duration", 0))


def max_sleeping_sync_duration_func(assemblies_values):
    return assemblies_values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + assemblies_values["update"].get("total_event_sleeping_wait_all_duration", 0)


def max_execution_sync_duration_func(assemblies_values):
    return (assemblies_values["deploy"].get("total_event_sleeping_wait_all_duration", 0) + assemblies_values["update"].get("total_event_sleeping_wait_all_duration", 0)
          + assemblies_values["deploy"].get("total_event_uptime_wait_all_duration", 0) + assemblies_values["update"].get("total_event_uptime_wait_all_duration", 0))


# Specific functions for central concerto-d
def max_deploy_duration_func_central(assemblies_values):
    return assemblies_values["deploy"].get("total_event_uptime_duration", 0)


def max_update_duration_func_central(assemblies_values):
    return assemblies_values["update"].get("total_event_uptime_duration", 0)


def max_reconf_duration_func_central(assemblies_values):
    return assemblies_values["deploy"].get("total_event_uptime_duration", 0) + assemblies_values["update"].get("total_event_uptime_duration", 0)
