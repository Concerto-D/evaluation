from concerto import global_variables
from concerto.assembly import Assembly
from concerto.time_logger import create_timestamp_metric, TimestampType
from synthetic_use_case import reconf_programs
from synthetic_use_case.openstack.assemblies.keystone_assembly import KeystoneAssembly


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc: Assembly, scaling_num: int):
    sc.add_component(f"keystone{scaling_num}", "Keystone")
    sc.connect(f"keystone{scaling_num}", "worker_service", f"mariadbworker{scaling_num}", "service")
    sc.connect(f"keystone{scaling_num}", "service", f"glance{scaling_num}", "keystone_service")
    sc.connect(f"keystone{scaling_num}", "service", f"nova{scaling_num}", "keystone_service")
    sc.connect(f"keystone{scaling_num}", "service", f"neutron{scaling_num}", "keystone_service")
    sc.push_b(f"keystone{scaling_num}", "deploy")
    sc.wait(f"keystone{scaling_num}")


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc, scaling_num: int):
    sc.push_b(f"keystone{scaling_num}", "stop")
    sc.wait(f"mariadbworker{scaling_num}", wait_for_refusing_provide=True)
    sc.push_b(f"keystone{scaling_num}", "deploy")
    sc.wait(f"keystone{scaling_num}")


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
    sc = KeystoneAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    if reconfiguration_name == "deploy":
        deploy(sc, scaling_num)
    else:
        update(sc, scaling_num)
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
