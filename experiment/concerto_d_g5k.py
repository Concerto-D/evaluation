import atexit
import os
import shutil
import subprocess
import time
from os.path import exists
from typing import List, Optional

import enoslib as en
from enoslib.infra.enos_g5k.g5k_api_utils import get_cluster_site

from experiment import globals_variables, log_experiment


def destroy_provider_from_job_name(job_name: str):
    conf = en.G5kConf.from_settings(job_name=job_name).finalize()
    provider = en.G5k(conf)
    provider.destroy()


def reserve_node_for_deployment(cluster: str):
    # _ = en.init_logging()
    site = get_cluster_site(cluster)
    base_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime="00:10:00", job_name="concerto_d_deployment")
                  .add_network_conf(base_network)
    )
    conf = conf.add_machine(
        roles=["deployment"],
        cluster=cluster,
        nodes=1,
        primary_network=base_network,
    )
    conf = conf.finalize()

    provider = en.G5k(conf)
    roles, networks = provider.init()
    return roles, networks, provider


def reserve_node_for_controller(job_name: str, cluster: str, walltime: str = '01:00:00', reservation: Optional[str] = None):
    # _ = en.init_logging()
    site = get_cluster_site(cluster)
    base_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime=walltime, reservation=reservation, job_name=job_name)
                  .add_network_conf(base_network)
    )
    conf = conf.add_machine(
        roles=["controller"],
        cluster=cluster,
        nodes=1,
        primary_network=base_network,
    )
    conf = conf.finalize()

    provider = en.G5k(conf)
    roles, networks = provider.init()
    return roles, networks, provider


def reserve_nodes_for_concerto_d(job_name: str, nb_concerto_d_nodes: int, nb_zenoh_routers: int, cluster: str, walltime: str = '01:00:00', reservation: Optional[str] = None):
    """
    TODO: voir pour les restriction des ressources (pour approcher des ressources d'une OU (raspberry ou autre))
    """
    # _ = en.init_logging()
    site = get_cluster_site(cluster)
    concerto_d_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    # TODO: le walltime, le mettre jusqu'à 9am du jour d'après pour tous les noeuds
    # TODO: faire les réservations en avance pour toutes les expés (master + noeuds de l'expé), en amont dans un autre
    # script (voir aussi script Maverick + voir si on peut retrouver le provider depuis la conf).
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime=walltime, reservation=reservation, job_name=job_name)
                  .add_network_conf(concerto_d_network)
    )
    conf = conf.add_machine(
        roles=["concerto_d", "server"],
        cluster=cluster,
        nodes=1,
        primary_network=concerto_d_network,
    )
    for i in range(nb_concerto_d_nodes - 1):
        conf = conf.add_machine(
            roles=["concerto_d", f"dep{i}"],
            cluster=cluster,
            nodes=1,
            primary_network=concerto_d_network,
        )
    conf = conf.add_machine(
        roles=["zenoh_routers"],
        cluster=cluster,
        nodes=nb_zenoh_routers,
        primary_network=concerto_d_network,
    )
    conf = conf.finalize()

    provider = en.G5k(conf)
    roles, networks = provider.init()
    return roles, networks


# def install_apt_deps(roles_concerto_d: List):
#     with en.actions(roles=roles_concerto_d) as a:
#         a.apt(name=["python3", "git"], state="present")
#         log_experiment.log.debug(a.results)


# def put_assemblies_configuration_file(role_controller, configuration_file_path: str):
#     with en.actions(roles=role_controller) as a:
#         home_dir = globals_variables.homedir
#         a.copy(src=configuration_file_path, dest=f"{home_dir}/concertonode/{configuration_file_path}")
#         log_experiment.log.debug(a.results)


def put_file(role_controller, uptimes_src: str, uptimes_dst: str):
    with en.actions(roles=role_controller) as a:
        a.copy(src=f"{uptimes_src}", dest=f"{globals_variables.g5k_executions_expe_logs_dir}/{uptimes_dst}")
        log_experiment.log.debug(a.results)


def initialize_expe_repositories(role_controller):
    home_dir = globals_variables.g5k_executions_expe_logs_dir
    with en.actions(roles=role_controller) as a:
        a.git(dest=f"{home_dir}/concerto-decentralized",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/concerto-decentralized.git",
              accept_hostkey=True)
        a.pip(chdir=f"{home_dir}/concerto-decentralized",
              requirements=f"{home_dir}/concerto-decentralized/requirements.txt",
              virtualenv=f"{home_dir}/concerto-decentralized/venv")
        a.git(dest=f"{home_dir}/evaluation",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/evaluation.git",
              accept_hostkey=True)
        a.git(dest=f"{home_dir}/experiment_files",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/experiment_files.git",
              accept_hostkey=True)


def install_zenoh_router(roles_zenoh_router: List):
    with en.actions(roles=roles_zenoh_router) as a:
        a.apt_repository(repo="deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /", state="present")
        a.apt(name="zenoh", update_cache="yes")
        log_experiment.log.debug(a.results)


def execute_reconf(role_node, version_concerto_d, config_file_path: str, duration: float, timestamp_log_file: str, nb_concerto_nodes, dep_num, waiting_rate: float, reconfiguration_name: str, environment: str):
    command_args = []
    if environment == "remote":
        command_args.append(f"PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/../evaluation")  # Set PYTHONPATH (equivalent of source set_python_path.sh)
    command_args.append("venv/bin/python3")               # Execute inside the python virtualenv
    assembly_name = "server" if dep_num is None else "dep"
    command_args.append(f"../evaluation/synthetic_use_case/reconf_programs/reconf_{assembly_name}.py")  # The reconf program to execute
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(str(duration))     # The awakening time of the program, it goes to sleep afterwards (it exits)
    command_args.append(str(waiting_rate))
    command_args.append(timestamp_log_file)
    command_args.append(globals_variables.g5k_execution_params_dir)
    command_args.append(version_concerto_d)
    command_args.append(reconfiguration_name)
    command_args.append(str(nb_concerto_nodes))
    if dep_num is not None:
        command_args.append(str(dep_num))  # If it's a dependency

    command_str = " ".join(command_args)
    home_dir = globals_variables.g5k_executions_expe_logs_dir
    if environment == "remote":
        with en.actions(roles=role_node) as a:
            exit_code = a.shell(chdir=f"{home_dir}/concerto-decentralized", command=command_str)
    else:
        cwd = os.getcwd()
        env_process = os.environ.copy()
        env_process["PYTHONPATH"] += f":{cwd}:{cwd}/../evaluation"
        process = subprocess.Popen(command_args, env=env_process, cwd=f"{home_dir}/concerto-decentralized")
        exit_code = process.wait()

    return exit_code


def kill_subprocess_on_exit(subproc):
    def _kill_subprocess():
        subproc.kill()

    return _kill_subprocess


def execute_zenoh_routers(roles_zenoh_router, timeout, environment):
    log_experiment.log.debug(f"launch zenoh routers with {timeout} timeout")
    kill_previous_routers_cmd = "kill $(ps -ef | grep -v grep | grep -w zenohd | awk '{print $2}')"
    launch_router_cmd = " ".join(["timeout", str(timeout), "zenohd", "--mem-storage='/**'"])

    if environment == "remote":
        en.run_command(kill_previous_routers_cmd, roles=roles_zenoh_router, on_error_continue=True)
        en.run_command(launch_router_cmd, roles=roles_zenoh_router, background=True)
    else:
        print("kill process")
        kill_process = subprocess.Popen(kill_previous_routers_cmd, shell=True)
        kill_process.wait()
        time.sleep(.5)
        print(f"process killed: {kill_process}")
        subprocess.Popen(launch_router_cmd, shell=True)


# TODO: refacto les dep/server names
def build_finished_reconfiguration_path(assembly_name, dep_num):
    if dep_num is None:
        return f"finished_reconfigurations/{assembly_name}_assembly"
    else:
        return f"finished_reconfigurations/{assembly_name.replace(str(dep_num), '')}_assembly_{dep_num}"


def fetch_finished_reconfiguration_file(role_node, assembly_name, dep_num, environment):
    src = f"{globals_variables.g5k_execution_params_dir}/{build_finished_reconfiguration_path(assembly_name, dep_num)}"
    dst = f"{globals_variables.local_execution_params_dir}/{build_finished_reconfiguration_path(assembly_name, dep_num)}"
    if environment == "remote":
        with en.actions(roles=role_node) as a:
            a.fetch(src=src, dest=dst, flat="yes", fail_on_missing="no")
    else:
        if exists(src):
            os.makedirs(f"{globals_variables.local_execution_params_dir}/finished_reconfigurations", exist_ok=True)
            shutil.copy(src, dst)


def build_times_log_path(assembly_name, dep_num, timestamp_log_file: str):
    # return f"{assembly_name}_{timestamp_log_file}.yaml"
    if dep_num is None:
        return f"{assembly_name}_{timestamp_log_file}.yaml"
    else:
        return f"dep{dep_num}_{timestamp_log_file}.yaml"


def fetch_times_log_file(role_node, assembly_name, dep_num, timestamp_log_file: str, reconfiguration_name: str, environment):
    src = f"{globals_variables.g5k_execution_params_dir}/{build_times_log_path(assembly_name, dep_num, timestamp_log_file)}"
    dst_dir = f"{globals_variables.local_execution_params_dir}/logs_files_assemblies/{reconfiguration_name}"
    dst = f"{dst_dir}/{build_times_log_path(assembly_name, dep_num, timestamp_log_file)}"
    if environment == "remote":
        with en.actions(roles=role_node) as a:
            a.fetch(src=src, dest=dst, flat="yes")
    else:
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy(src, dst)
