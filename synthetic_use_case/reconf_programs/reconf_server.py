from concerto import time_logger
from concerto.time_logger import TimeToSave
from synthetic_use_case.assemblies.server_assembly import ServerAssembly

from synthetic_use_case.reconf_programs import reconf_programs


def deploy(sc, nb_deps_tot):
    time_logger.log_time_value(TimeToSave.START_DEPLOY)
    sc._p_id_sync = 0
    sc.add_component("server", sc.server)
    for dep_num in range(nb_deps_tot):
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
    sc.push_b("server", "deploy")
    sc.wait_all()
    time_logger.log_time_value(TimeToSave.END_DEPLOY)


def update(sc):
    time_logger.log_time_value(TimeToSave.START_UPDATE)
    sc._p_id_sync = 1
    sc.push_b("server", "suspend")
    sc.wait_all(wait_for_refusing_provide=True)
    sc.push_b("server", "deploy")
    sc.wait_all()
    time_logger.log_time_value(TimeToSave.END_UPDATE)


def execute_reconf(config_dict, duration, waiting_rate, version_concerto_d):
    sc = ServerAssembly(config_dict, waiting_rate, version_concerto_d)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    deploy(sc, config_dict["nb_deps_tot"])
    update(sc)
    sc.finish_reconfiguration()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(config_dict, duration, waiting_rate, version_concerto_d)
    time_logger.log_time_value(TimeToSave.SLEEP_TIME)
