import sys

from concerto import debug_logger
from concerto.time_logger import TimestampType, create_timestamp_metric
from synthetic_use_case.assemblies.server_clients_assembly import ServerClientsAssembly

from synthetic_use_case.reconf_programs import reconf_programs


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc, nb_deps_tot):
    sc.add_component("server", "Server")
    for dep_num in range(nb_deps_tot):
        sc.add_component(f"dep{dep_num}", "Dep")
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
        sc.push_b(f"dep{dep_num}", "deploy")
    sc.push_b("server", "deploy")
    sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc):
    sc.push_b("server", "suspend")
    sc.push_b("server", "deploy")
    sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, uptimes_nodes_file_path):
    sc = ServerClientsAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, uptimes_nodes_file_path)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, nb_concerto_nodes)
    else:
        update(sc)

    return sc


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num, uptimes_nodes_file_path = reconf_programs.initialize_reconfiguration()
    debug_logger.log.debug(f"Central reconf, getting uptims_nodes_file_path: {uptimes_nodes_file_path}")

    sc = execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, uptimes_nodes_file_path)
    sc.finish_reconfiguration()
