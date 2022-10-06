from concerto.time_logger import TimestampType, create_timestamp_metric
from synthetic_use_case.assemblies.server_assembly import ServerAssembly

from synthetic_use_case.reconf_programs import reconf_programs


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc, version_concerto_d, nb_deps_tot):
    sc.add_component("server", "Server")
    for dep_num in range(nb_deps_tot):
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
    sc.push_b("server", "deploy")
    if version_concerto_d == "asynchronous":
        sc.wait("server")
    else:
        sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc, version_concerto_d):
    sc.push_b("server", "suspend")
    sc.wait_all(wait_for_refusing_provide=True)
    sc.push_b("server", "deploy")
    if version_concerto_d == "asynchronous":
        sc.wait("server")
    else:
        sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
    sc = ServerAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, version_concerto_d, nb_concerto_nodes)
    else:
        update(sc, version_concerto_d)
    sc.finish_reconfiguration()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
