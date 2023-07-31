from concerto import global_variables
from concerto.time_logger import TimestampType, create_timestamp_metric
from synthetic_use_case.parallel_deps.assemblies.server_assembly import ServerAssembly

from synthetic_use_case import reconf_programs


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc, nb_deps_tot):
    sc.add_component("server", "Server")
    for dep_num in range(nb_deps_tot):
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
    sc.push_b("server", "deploy")
    sc.wait("server")


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc, nb_deps_tot):
    sc.push_b("server", "suspend")
    sc.wait_all(wait_for_refusing_provide=True, deps_concerned=[(f"dep{dep_num}", "service") for dep_num in range(nb_deps_tot)])
    sc.push_b("server", "deploy")
    sc.wait("server")


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
    sc = ServerAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, nb_concerto_nodes)
    else:
        update(sc, nb_concerto_nodes)

    return sc


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME_WAIT_ALL)
def execute_global_sync(sc):
    sc.exit_code_sleep = 5
    sc.wait_all()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num, _, _ = reconf_programs.initialize_reconfiguration()
    sc = execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    if not global_variables.is_concerto_d_asynchronous():
        execute_global_sync(sc)
    sc.finish_reconfiguration()
