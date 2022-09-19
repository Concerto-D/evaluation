from concerto import time_logger
from concerto.time_logger import TimeToSave
from synthetic_use_case.assemblies.dep_assembly import DepAssembly

from synthetic_use_case.reconf_programs import reconf_programs
from synthetic_use_case.reconf_programs.reconf_programs import handle_sleeping_behavior


@handle_sleeping_behavior(TimeToSave.END_DEPLOY)
def deploy(sc, dep_num):
    time_logger.log_time_value(TimeToSave.START_DEPLOY)
    sc.id_sync = 0
    sc.add_component(f"dep{dep_num}", "Dep")
    sc.connect(f"dep{dep_num}", "ip", "server", f"serviceu_ip{dep_num}")
    sc.connect(f"dep{dep_num}", "service", "server", f"serviceu{dep_num}")
    sc.push_b(f"dep{dep_num}", "deploy")
    sc.wait_all()
    time_logger.log_time_value(TimeToSave.END_DEPLOY)


@handle_sleeping_behavior(TimeToSave.END_UPDATE)
def update(sc, dep_num):
    time_logger.log_time_value(TimeToSave.START_UPDATE)
    sc.id_sync = 1
    sc.push_b(f"dep{dep_num}", "update")
    sc.push_b(f"dep{dep_num}", "deploy")
    sc.wait_all()
    time_logger.log_time_value(TimeToSave.END_UPDATE)


def execute_reconf(dep_num, config_dict, duration, waiting_rate, version_concerto_d):
    sc = DepAssembly(dep_num, config_dict, waiting_rate, version_concerto_d)
    sc.set_verbosity(2)
    sc.time_manager.start(duration)
    deploy(sc, dep_num)
    update(sc, dep_num)
    sc.finish_reconfiguration()


if __name__ == '__main__':
    config_dict, duration, waiting_rate, version_concerto_d, dep_num = reconf_programs.initialize_reconfiguration()
    execute_reconf(dep_num, config_dict, duration, waiting_rate, version_concerto_d)
    time_logger.log_time_value(TimeToSave.SLEEP_TIME)
