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
    # _ = en.init_logging()
    site = get_cluster_site(cluster)
    concerto_d_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
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

def add_host_keys_to_know_hosts(roles_concerto_d, cluster):
    site = get_cluster_site(cluster)
    log = log_experiment.log
    log.debug(f"Check host keys for nodes in {site}")
    for k, v in roles_concerto_d.items():
        if k != "concerto_d":
            log.debug(f"Check {v[0].address}")
            process = subprocess.Popen(
                f"ssh-keygen -F {v[0].address}",
                shell=True
            )
            res = process.wait()
            host_key_exists = res == 0
            if not host_key_exists:
                known_hosts_file = "~/.ssh/known_hosts"
                log.debug(f"Host key doesn't exists, add {v[0].address} to {known_hosts_file}")
                process_keyscan = subprocess.Popen(
                    f"ssh {site}.grid5000.fr 'ssh-keyscan {v[0].address}' >> {known_hosts_file}",
                    shell=True
                )
                process_keyscan.wait()
                log.debug("Added")


def put_file(role_controller, src: str, dst: str):
    with en.actions(roles=role_controller) as a:
        a.copy(src=src, dest=dst)
        log_experiment.log.debug(a.results)


def initialize_expe_repositories(version_concerto_d, role_controller):
    home_dir = globals_variables.g5k_executions_expe_logs_dir
    with en.actions(roles=role_controller) as a:
        if version_concerto_d == "mjuz":
            a.git(dest=f"{home_dir}/mjuz-concerto-d",
                  repo="https://gitlab.inria.fr/aomond/mjuz-concerto-d.git",
                  version="custom_provider",
                  accept_hostkey=True)
        else:
            a.git(dest=f"{home_dir}/concerto-decentralized",
                  repo="https://gitlab.inria.fr/aomond-imt/concerto-d/concerto-decentralized.git",
                  accept_hostkey=True)
            a.pip(chdir=f"{home_dir}/concerto-decentralized",
                  requirements=f"{home_dir}/concerto-decentralized/requirements.txt",
                  virtualenv=f"{home_dir}/concerto-decentralized/venv")
        # a.git(dest=f"{home_dir}/evaluation",
        #       repo="https://gitlab.inria.fr/aomond-imt/concerto-d/evaluation.git",
        #       accept_hostkey=True)
        a.git(dest=f"{home_dir}/experiment_files",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/experiment_files.git",
              accept_hostkey=True)
        log_experiment.log.debug(a.results)


def initialize_deps_mjuz(roles_concerto_d):
    home_dir = globals_variables.g5k_executions_expe_logs_dir
    with en.actions(roles=roles_concerto_d) as a:
        a.apt(
            name="npm",
            update_cache="yes"
        )
        # Need to pass as dict due to reserved keyword: global
        a.npm(
            **{
                "global": "yes",
                "name": "yarn",
            }
        )
        a.npm(
            **{
                "global": "yes",
                "name": "ts-node",
            }
        )
        a.copy(
            src="/home/anomond/pulumi-mjuz/pulumi",
            dest="/opt",
            remote_src="yes",
        )

    en.run_command(
        f"cd {home_dir}/mjuz-concerto-d && yarn && yarn build", roles=roles_concerto_d[0]
    )

    with en.actions(roles=roles_concerto_d) as a:
        a.copy(
            src=f"{home_dir}/mjuz-concerto-d",
            dest="/",
            remote_src="yes"
        )


def install_zenoh_router(roles_zenoh_router: List):
    """
    Install the 0.6 version of zenoh router
    """
    with en.actions(roles=roles_zenoh_router) as a:
        a.apt_repository(repo="deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /", state="present")
        a.apt(name="zenoh", update_cache="yes")
        log_experiment.log.debug(a.results)


def execute_reconf(role_node, version_concerto_d, config_file_path: str, duration: float, timestamp_log_file: str, nb_concerto_nodes, dep_num, waiting_rate: float, reconfiguration_name: str, environment: str):
    command_args = []
    home_dir = globals_variables.g5k_executions_expe_logs_dir
    if environment == "remote":
        command_args.append(f"cd {home_dir}/concerto-decentralized;")
        command_args.append(f"export PYTHONPATH=$PYTHONPATH:{home_dir}/evaluation;")
    command_args.append(f"{home_dir}/concerto-decentralized/venv/bin/python3")               # Execute inside the python virtualenv
    assembly_name = "server" if dep_num is None else "dep"
    command_args.append(f"{home_dir}/evaluation/synthetic_use_case/reconf_programs/reconf_{assembly_name}.py")  # The reconf program to execute
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
    if environment == "remote":
        process = subprocess.Popen(f"ssh anomond@{role_node[0].address} '{command_str}'", shell=True)
        exit_code = process.wait()

    else:
        cwd = os.getcwd()
        env_process = os.environ.copy()
        env_process["PYTHONPATH"] += f":{cwd}:{cwd}/../evaluation"
        process = subprocess.Popen(command_args, env=env_process, cwd=f"{home_dir}/concerto-decentralized")
        exit_code = process.wait()

    if exit_code not in [0, 5, 50]:
        raise Exception(f"Unexpected exit code for the the role: {role_node[0].address} ({assembly_name}{dep_num}): {exit_code}")

    return exit_code


def execute_mjuz_reconf(role_node, version_concerto_d, config_file_path: str, duration: float, timestamp_log_file: str, nb_concerto_nodes, dep_num, waiting_rate: float, reconfiguration_name: str, environment: str):
    command_args = []
    assembly_name = "server" if dep_num is None else "dep"

    mjuz_dir = "/mjuz-concerto-d" if environment == "remote" else f"{globals_variables.g5k_executions_expe_logs_dir}/mjuz-concerto-d"
    command_args.append("/opt/pulumi/bin/pulumi login file:///tmp;")
    command_args.append(f"cd {mjuz_dir}/synthetic-use-case/{assembly_name};")
    trailing = "" if environment == "remote" else ""
    command_args.append("PATH=$PATH:/opt/pulumi:/opt/pulumi/bin" + trailing)
    command_args.append("PULUMI_SKIP_UPDATE_CHECK=1" + trailing)
    command_args.append("PULUMI_AUTOMATION_API_SKIP_VERSION_CHECK=0" + trailing)
    command_args.append("PULUMI_CONFIG_PASSPHRASE=0000" + trailing)
    command_args.append(f"ts-node . -v trace")
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(timestamp_log_file)
    command_args.append(globals_variables.g5k_execution_params_dir)
    command_args.append(reconfiguration_name)
    command_args.append(str(nb_concerto_nodes))
    if dep_num is not None:
        command_args.append(str(dep_num))  # If it's a dependency

    command_str = " ".join(command_args)
    if environment == "remote":
        process = subprocess.Popen(f"ssh root@{role_node[0].address} '{command_str}'", shell=True)
    else:
        process = subprocess.Popen(command_str, shell=True)
    exit_code = process.wait()

    if exit_code not in [0, 5, 50]:
        raise Exception(f"Unexpected exit code for the the role: {role_node[0].address} ({assembly_name}{dep_num}): {exit_code}")

    return exit_code


def kill_subprocess_on_exit(subproc):
    def _kill_subprocess():
        subproc.kill()

    return _kill_subprocess


def execute_zenoh_routers(roles_zenoh_router, timeout, environment):
    log_experiment.log.debug(f"launch zenoh routers with {timeout} timeout")
    kill_previous_routers_cmd = "kill $(ps -ef | grep -v grep | grep -w zenohd | awk '{print $2}')"
    concerto_d_projects_dir = globals_variables.g5k_executions_expe_logs_dir if environment == "remote" else globals_variables.all_experiments_results_dir
    launch_router_cmd = " ".join(["timeout", str(timeout), "zenohd", "-c", f"{concerto_d_projects_dir}/evaluation/experiment/zenohd-config.json5"])

    if environment == "remote":
        en.run_command(kill_previous_routers_cmd, roles=roles_zenoh_router, on_error_continue=True)
        time.sleep(1)
        en.run_command(launch_router_cmd, roles=roles_zenoh_router, background=True)
    else:
        log_experiment.log.debug("kill process")
        kill_process = subprocess.Popen(kill_previous_routers_cmd, shell=True)
        kill_process.wait()
        time.sleep(1)
        log_experiment.log.debug(f"process killed: {kill_process}")
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
        process = subprocess.Popen(f"scp {role_node[0].address}:{src} {dst}", shell=True)
        exit_code = process.wait()
        if exit_code != 0:
            raise Exception(f"Error while fetch log_file_assembly (src: {src}, dst: {dst})")
    else:
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy(src, dst)


def clean_previous_mjuz_environment(roles_concerto_d, environment):
    """
    Delete and recreate ~/.pulumi dir (containing state of deployed infrastructure) + kill all running
    ts-node processes
    """
    kill_ts_node_cmd = "kill -9 $(ps -aux | pgrep -f ts-node)"
    reset_pulumi_dir_cmd = f"rm -rf /tmp/.pulumi &&"
    trailing = ";" if environment == "remote" else ""
    reset_pulumi_dir_cmd += " PULUMI_SKIP_UPDATE_CHECK=1" + trailing
    reset_pulumi_dir_cmd += " PULUMI_AUTOMATION_API_SKIP_VERSION_CHECK=0" + trailing
    reset_pulumi_dir_cmd += " /opt/pulumi/bin/pulumi login file:///tmp"

    if environment == "remote":
        en.run_command(kill_ts_node_cmd, roles=roles_concerto_d, on_error_continue=True)
        en.run_command(reset_pulumi_dir_cmd, roles=roles_concerto_d)

    else:
        subprocess.Popen(kill_ts_node_cmd, shell=True).wait()
        subprocess.Popen(reset_pulumi_dir_cmd, shell=True).wait()

