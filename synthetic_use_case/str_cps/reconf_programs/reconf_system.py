from concerto import global_variables
from concerto.assembly import Assembly
from concerto.time_logger import create_timestamp_metric, TimestampType
from synthetic_use_case import reconf_programs
from synthetic_use_case.str_cps.assemblies.system_assembly import SystemAssembly


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc: Assembly, nb_concerto_nodes: int):
    sc.add_component("system", "System")
    sc.connect("system", "system_service_use", "database", "database_service_provide")
    for i in range(nb_concerto_nodes):
        sc.connect("system", "system_service_provide", f"listener{i}", "listener_service_use")
    sc.push_b("system", "deploy")
    sc.wait("system")


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc):
    sc.push_b("system", "update")
    sc.wait("database", wait_for_refusing_provide=True)
    sc.push_b("system", "deploy")
    sc.wait("system")


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
    sc = SystemAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, nb_concerto_nodes)
    else:
        update(sc)
    return sc


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME_WAIT_ALL)
def execute_global_sync(sc):
    sc.exit_code_sleep = 5
    sc.wait_all()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num, _, _ = reconf_programs.initialize_reconfiguration()
    sc = execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
    if not global_variables.is_concerto_d_asynchronous():
        execute_global_sync(sc)
    sc.finish_reconfiguration()
