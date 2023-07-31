from concerto import global_variables
from concerto.assembly import Assembly
from concerto.time_logger import create_timestamp_metric, TimestampType
from synthetic_use_case import reconf_programs
from synthetic_use_case.str_cps.assemblies.database_assembly import DatabaseAssembly


@create_timestamp_metric(TimestampType.TimestampEvent.DEPLOY)
def deploy(sc: Assembly):
    sc.add_component("database", "Database")
    sc.connect("database", "database_service_provide", "system", "system_service_use")
    sc.push_b("database", "deploy")
    sc.wait(f"database")


@create_timestamp_metric(TimestampType.TimestampEvent.UPDATE)
def update(sc):
    sc.push_b(f"database", "interrupt")
    sc.push_b(f"database", "update")
    sc.push_b(f"database", "deploy")
    sc.wait(f"database")


@create_timestamp_metric(TimestampType.TimestampEvent.UPTIME)
def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
    sc = DatabaseAssembly(config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
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
    config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num, _, _ = reconf_programs.initialize_reconfiguration()
    sc = execute_reconf(config_dict, duration, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num)
    if not global_variables.is_concerto_d_asynchronous():
        execute_global_sync(sc)
    sc.finish_reconfiguration()
