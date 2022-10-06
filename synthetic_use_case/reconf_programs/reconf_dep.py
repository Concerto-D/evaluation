from synthetic_use_case.assemblies.dep_assembly import DepAssembly

from synthetic_use_case.reconf_programs import reconf_programs
from concerto.time_logger import TimestampType, create_timestamp_metric


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc, version_concerto_d, dep_num):
    sc.add_component(f"dep{dep_num}", "Dep")
    sc.connect(f"dep{dep_num}", "ip", "server", f"serviceu_ip{dep_num}")
    sc.connect(f"dep{dep_num}", "service", "server", f"serviceu{dep_num}")
    sc.push_b(f"dep{dep_num}", "deploy")
    if version_concerto_d == "asynchronous":
        sc.wait(f"dep{dep_num}")
    else:
        sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc, version_concerto_d, dep_num):
    sc.push_b(f"dep{dep_num}", "update")
    sc.push_b(f"dep{dep_num}", "deploy")
    if version_concerto_d == "asynchronous":
        sc.wait(f"dep{dep_num}")
    else:
        sc.wait_all()


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(dep_num, config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
    sc = DepAssembly(dep_num, config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, version_concerto_d, dep_num)
    else:
        update(sc, version_concerto_d, dep_num)
    sc.finish_reconfiguration()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(dep_num, config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes)
