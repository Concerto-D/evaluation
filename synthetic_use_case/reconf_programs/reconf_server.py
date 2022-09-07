from concerto import time_logger
from concerto.time_logger import TimeToSave
from synthetic_use_case.assemblies.server_assembly import ServerAssembly

from synthetic_use_case.reconf_programs import reconf_programs


def deploy(sc, nb_deps_tot):
    # _p_id_sync = 0
    sc.add_component("server", sc.server)
    for dep_num in range(nb_deps_tot):
        sc.connect("server", f"serviceu_ip{dep_num}", f"dep{dep_num}", "ip")
        sc.connect("server", f"serviceu{dep_num}", f"dep{dep_num}", "service")
    sc.push_b("server", "deploy")
    sc.wait_all()


def update(sc):
    # _p_id_sync = 1
    sc.push_b("server", "suspend")
    sc.wait_all(wait_for_refusing_provide=True)
    sc.push_b("server", "deploy")
    sc.wait_all()


def execute_reconf(config_dict, duration, waiting_rate):
    sc = ServerAssembly(config_dict, waiting_rate)
    sc.set_verbosity(2)
    deploy(sc, config_dict["nb_deps_tot"])
    update(sc)
    sc.execute_reconfiguration_program(duration)


if __name__ == '__main__':
    config_dict, duration, waiting_rate, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(config_dict, duration, waiting_rate)
    time_logger.log_time_value(TimeToSave.SLEEP_TIME)
