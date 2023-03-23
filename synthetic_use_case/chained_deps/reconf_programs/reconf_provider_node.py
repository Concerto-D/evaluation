import time

from concerto import global_variables
from concerto.time_logger import create_timestamp_metric, TimestampType
from synthetic_use_case import reconf_programs
from synthetic_use_case.chained_deps.assemblies.provider_node_assembly import ProviderNodeAssembly


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc):
    print("deploying")
    time.sleep(5)
    print("done")
    return


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc):
    print("updating")
    time.sleep(3)
    print("done")
    return


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
    sc = ProviderNodeAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc)
    else:
        update(sc)
    return sc


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME_WAIT_ALL)
def execute_global_sync(sc):
    sc.exit_code_sleep = 5
    sc.wait_all()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, _, _, _ = reconf_programs.initialize_reconfiguration()
    sc = execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    if not global_variables.is_concerto_d_asynchronous():
        execute_global_sync(sc)
    sc.finish_reconfiguration()
