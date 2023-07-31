from concerto import global_variables
from concerto.assembly import Assembly
from concerto.time_logger import create_timestamp_metric, TimestampType
from synthetic_use_case import reconf_programs
from synthetic_use_case.str_cps.assemblies.listener_assembly import ListenerAssembly


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc: Assembly, scaling_num: int):
    sc.add_component(f"listener{scaling_num}", "Listener")
    sc.connect(f"listener{scaling_num}", "listener_service_use", "system", "system_service_provide")
    sc.connect(f"listener{scaling_num}", "listener_config_provide", f"sensor{scaling_num}", "sensor_config_use")
    sc.connect(f"listener{scaling_num}", "listener_service_provide", f"sensor{scaling_num}", "sensor_service_use")
    sc.push_b(f"listener{scaling_num}", "deploy")
    sc.wait(f"listener{scaling_num}")


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc, scaling_num: int):
    sc.push_b(f"listener{scaling_num}", "update")
    sc.wait("system", wait_for_refusing_provide=True)
    sc.push_b(f"listener{scaling_num}", "deploy")
    sc.wait(f"listener{scaling_num}")


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
    sc = ListenerAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
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
