from concerto import time_logger
from concerto.time_logger import TimeToSave
from synthetic_use_case.assemblies.dep_assembly import DepAssembly

from synthetic_use_case.reconf_programs import reconf_programs


def deploy(sc, dep_num):
    # _p_id_sync = 0
    sc._p_id_sync = 0
    sc.add_component(f"dep{dep_num}", sc.dep)
    sc.connect(f"dep{dep_num}", "ip", "server", f"serviceu_ip{dep_num}")
    sc.connect(f"dep{dep_num}", "service", "server", f"serviceu{dep_num}")
    sc.push_b(f"dep{dep_num}", "deploy")
    sc.wait_all()


def update(sc, dep_num):
    # _p_id_sync = 1
    sc._p_id_sync = 1
    sc.push_b(f"dep{dep_num}", "update")
    sc.push_b(f"dep{dep_num}", "deploy")
    sc.wait_all()


def execute_reconf(dep_num, config_dict, duration, waiting_rate):
    sc = DepAssembly(dep_num, config_dict, waiting_rate)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    deploy(sc, dep_num)
    update(sc, dep_num)
    sc.finish_reconfiguration()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(dep_num, config_dict, duration, waiting_rate)
    time_logger.log_time_value(TimeToSave.SLEEP_TIME)
