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


def reserve_nodes_for_concerto_d(job_name: str, nb_server_clients: int, nb_servers: int, nb_dependencies: int, nb_zenoh_routers: int, cluster: str, walltime: str = '01:00:00', reservation: Optional[str] = None):
    # TODO: refacto assembly_name
    _ = en.init_logging()
    site = get_cluster_site(cluster)
    concerto_d_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime=walltime, reservation=reservation, job_name=job_name)
                  .add_network_conf(concerto_d_network)
    )
    conf = conf.add_machine(
        roles=["concerto_d", "server"],
        cluster=cluster,
        nodes=nb_servers,
        primary_network=concerto_d_network,
    )
    for i in range(nb_dependencies):
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
    conf = conf.add_machine(
        roles=["concerto_d", "server-clients"],
        cluster=cluster,
        nodes=nb_server_clients,
        primary_network=concerto_d_network,
    )
    conf = conf.finalize()

    provider = en.G5k(conf)
    roles, networks = provider.init()
    return roles, networks, provider


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


def put_file(roles, src: str, dst: str, environment: str):
    if environment in ["remote", "raspberry"]:
        with en.actions(roles=roles) as a:
            a.copy(src=src, dest=dst)
            log_experiment.log.debug(a.results)
    else:
        shutil.copy(src, dst)


def create_dir(roles, dir_path: str, environment: str):
    """
    Create all dir hierarchy if it doesn't exists
    """
    if environment in ["remote", "raspberry"]:
        with en.actions(roles=roles) as a:
            a.file(path=dir_path, state="directory")
    else:
        os.makedirs(dir_path, exist_ok=True)


def initialize_expe_repositories(version_concerto_d, roles):
    all_executions_dir = globals_variables.all_executions_dir
    with en.actions(roles=roles) as a:
        a.apt(name=["git", "python3-pip", "virtualenv"], state="present")
        if version_concerto_d in ["mjuz", "mjuz-2-comps"]:
            a.git(dest=f"{all_executions_dir}/mjuz-concerto-d",
                  repo="https://github.com/Concerto-D/mjuz-concerto-d.git",
                  version="main",
                  accept_hostkey=True)
        else:
            a.git(dest=f"{all_executions_dir}/concerto-decentralized",
                  repo="https://github.com/Concerto-D/concerto-decentralized.git",
                  accept_hostkey=True)
            a.pip(chdir=f"{all_executions_dir}/concerto-decentralized",
                  requirements=f"{all_executions_dir}/concerto-decentralized/requirements.txt",
                  virtualenv=f"{all_executions_dir}/concerto-decentralized/venv")
        a.git(dest=f"{all_executions_dir}/evaluation",
              repo="https://github.com/Concerto-D/evaluation.git",
              version="main",
              accept_hostkey=True)
        a.git(dest=f"{all_executions_dir}/experiment_files",
              repo="https://github.com/Concerto-D/experiment_files.git",
              accept_hostkey=True)
        log_experiment.log.debug(a.results)


def initialize_deps_mjuz(roles_concerto_d, environment):
    all_executions_dir = globals_variables.all_executions_dir
    with en.actions(roles=roles_concerto_d) as a:
        a.apt(
            name="npm",
            update_cache="yes"
        )
        if environment == "raspberry":
            yarn_cmd = f"{globals_variables.all_executions_dir}/pulumi-bin/yarn"
        else:
            yarn_cmd = "yarn"
        # Need to pass as dict due to reserved keyword: global
        if environment == "remote":
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

            # TODO: change pulumi-mjuz location (instead of /opt)
            a.copy(
                src="/home/anomond/pulumi-mjuz/pulumi",
                dest="/opt",
                remote_src="yes",
            )
        else:
            a.npm(
                name="yarn",
                path=f"{globals_variables.all_executions_dir}"
            )
            a.npm(
                name="ts-node",
                path=f"{globals_variables.all_executions_dir}"
            )

            # Put link to yarn and ts-node in pulumi-bin dir
            a.file(
                src=f"{globals_variables.all_executions_dir}/node_modules/yarn/bin/yarn",
                dest=yarn_cmd,
                state="link"
            )
            a.file(
                src=f"{globals_variables.all_executions_dir}/node_modules/ts-node/dist/bin.js",
                dest=_get_ts_node_path(environment),
                state="link"
            )
    # TODO: check this solution: https://stackoverflow.com/questions/71420286/unable-to-install-grpc-tools-via-npm-or-yarn-on-mac-m1-chip

    # TODO: Need to add grpc-tools dependency again for g5k to build grpc deps instead of putting the prebuild binaries
    # Install dependencies
    en.run_command(
        f"cd {all_executions_dir}/mjuz-concerto-d && {yarn_cmd}", roles=roles_concerto_d
    )

    # TODO: check what is better: version dist/ folder or put dist/ on remote before execution
    # if environment == "raspberry":
    #     # Install pre-build grpc protos because grpc-tools not available on Raspberry (aarch64)
    #     with en.actions(roles=roles_concerto_d) as a:
    #         a.unarchive(
    #             src=f"{globals_variables.all_expes_dir}/all-bin-files/prebuild-grpc-protos.tar",
    #             dest=f"{globals_variables.all_executions_dir}/mjuz-concerto-d/node_modules/@mjuz/grpc-protos"
    #         )

    # Build project
    if environment == "remote":
        cmd_to_run = f"{yarn_cmd} build"
    else:
        # Don't build grpc-protos because grpc-tools not available on Raspberry (aarch64)
        cmd_to_run = f"{yarn_cmd} build-raspberry"

    en.run_command(
        f"cd {all_executions_dir}/mjuz-concerto-d && {cmd_to_run}", roles=roles_concerto_d
    )


def _get_zenoh_install_dir():
    return f"{globals_variables.all_executions_dir}/zenoh_install"


def _get_ts_node_path(environment: str):
    if environment in ["local", "remote"]:
        return "ts-node"  # Located in /usr/bin
    else:
        return f"{globals_variables.all_executions_dir}/pulumi-bin/ts-node"


def install_zenoh_router(roles_zenoh_router: List, environment: str):
    """
    Install the 0.6 version of zenoh router
    """
    zenoh_install_dir = _get_zenoh_install_dir()

    # Install dependencies and prepare zenoh install dir
    with en.actions(roles=roles_zenoh_router) as a:
        a.file(path=zenoh_install_dir, state="directory")
    put_file(roles_zenoh_router, f"{globals_variables.all_expes_dir}/evaluation/experiment/zenohd-config.json5", zenoh_install_dir, environment)

    # Installing zenoh in the executions dir
    with en.actions(roles=roles_zenoh_router) as a:
        a.apt(name="unzip", state="present")
        arch = "aarch64" if environment == "raspberry" else "x86_64"
        a.unarchive(remote_src="yes",
                    src=f"https://download.eclipse.org/zenoh/zenoh/0.6.0-beta.1/{arch}-unknown-linux-gnu/zenoh-0.6.0-beta.1-{arch}-unknown-linux-gnu.zip",
                    dest=zenoh_install_dir)
        log_experiment.log.debug(a.results)


def execute_reconf(
        role_node,
        version_concerto_d,
        config_file_path: str,
        duration: float,
        timestamp_log_file: str,
        nb_concerto_nodes,
        dep_num,
        waiting_rate: float,
        reconfiguration_name: str,
        environment: str,
        assembly_type: str,
        uptimes_file_name: str,
        execution_start_time: float,
        debug_current_uptime_and_overlap: str,
        use_case_name: str
):
    log = log_experiment.log
    command_args = []
    all_executions_dir = globals_variables.all_executions_dir
    if environment in ["remote", "raspberry"]:
        command_args.append(f"cd {all_executions_dir}/concerto-decentralized;")
        command_args.append(f"export PYTHONPATH=$PYTHONPATH:{all_executions_dir}/evaluation;")
    command_args.append(f"{all_executions_dir}/concerto-decentralized/venv/bin/python3")               # Execute inside the python virtualenv
    command_args.append(f"{all_executions_dir}/evaluation/synthetic_use_case/{use_case_name}/reconf_programs/reconf_{assembly_type}.py")  # The reconf program to execute
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(str(duration))     # The awakening time of the program, it goes to sleep afterwards (it exits)
    command_args.append(str(waiting_rate))
    command_args.append(timestamp_log_file)
    command_args.append(globals_variables.current_execution_dir)
    command_args.append(version_concerto_d)
    command_args.append(reconfiguration_name)
    command_args.append(str(nb_concerto_nodes))
    if dep_num is not None:  # If it's a dependency
        command_args.append("--dep_num")
        command_args.append(str(dep_num))

    if assembly_type == "server-clients":
        command_args.append("--uptimes_nodes_file_path")
        command_args.append(uptimes_file_name)

    if assembly_type == "server-clients":
        command_args.append("--execution_start_time")
        command_args.append(str(execution_start_time))

    command_args.append("--debug_current_uptime_and_overlap")
    command_args.append("\""+debug_current_uptime_and_overlap+"\"")

    command_args.append("--use_case_name")
    command_args.append(use_case_name)

    command_str = " ".join(command_args)
    command_str_to_log = " ".join(command_args[:-2])  # do not put the big list of overlaps between nodes (last 2 arg) in the experiments_logs
    log.debug(f"Start execution reconfiguration, command executed: {command_str_to_log}")
    if environment in ["remote", "raspberry"]:
        process = subprocess.Popen(f"ssh root@{role_node[0].address} '{command_str}'", shell=True)
        exit_code = process.wait()

    else:
        cwd = os.getcwd()
        env_process = os.environ.copy()
        env_process["PYTHONPATH"] += f":{cwd}:{cwd}/../evaluation"
        process = subprocess.Popen(command_args, env=env_process, cwd=f"{all_executions_dir}/concerto-decentralized")
        exit_code = process.wait()

    return exit_code


def execute_mjuz_reconf(
        role_node,
        version_concerto_d,
        config_file_path: str,
        duration: float,
        timestamp_log_file: str,
        nb_concerto_nodes,
        dep_num,
        waiting_rate: float,
        reconfiguration_name: str,
        environment: str,
        assembly_type: str
):
    # TODO: Ajouter le use_case_name pour Mjuz
    command_args = []

    mjuz_dir = f"{globals_variables.all_executions_dir}/mjuz-concerto-d"
    path_pulumi_bin = _get_pulumi_bin_path(environment)
    # command_args.append(f"{path_pulumi_bin}/pulumi login file:///tmp;")
    dir_name = f"cd {mjuz_dir}/synthetic-use-case/{assembly_type}"
    if "mjuz-2-comps":
        dir_name += "-2-components"
    command_args.append(dir_name + ";")
    trailing = "" if environment in ["remote", "raspberry"] else ""
    command_args.append(f"PATH=$PATH:{path_pulumi_bin}" + trailing)
    command_args.append("PULUMI_SKIP_UPDATE_CHECK=1" + trailing)
    command_args.append("PULUMI_AUTOMATION_API_SKIP_VERSION_CHECK=0" + trailing)
    command_args.append("PULUMI_CONFIG_PASSPHRASE=0000" + trailing)
    command_args.append(f"timeout --preserve-status -s 3 {duration}")

    command_args.append(f"{_get_ts_node_path(environment)} . -v trace")
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(str(duration))     # The awakening time of the program, it goes to sleep afterwards (it exits)
    command_args.append(timestamp_log_file)
    command_args.append(globals_variables.current_execution_dir)
    command_args.append(reconfiguration_name)
    command_args.append(str(nb_concerto_nodes))
    if dep_num is not None:
        command_args.append(str(dep_num))  # If it's a dependency

    command_str = " ".join(command_args)
    log_experiment.log.debug(f"Command launched: {command_str}")
    if environment in ["remote", "raspberry"]:
        process = subprocess.Popen(f"ssh root@{role_node[0].address} '{command_str}'", shell=True)
    else:
        process = subprocess.Popen(f"{command_str}", shell=True)

    # Magic value (timeout need to be above 90s min cause 88s is the amount of time need for server to deploy
    # but below 135 because it is the maximum sleeping time of the server)
    exit_code = process.wait(timeout=130)

    return exit_code


def kill_subprocess_on_exit(subproc):
    def _kill_subprocess():
        subproc.kill()

    return _kill_subprocess


def _get_pulumi_bin_path(environment: str):
    if environment in ["local", "remote"]:
        return "/opt/pulumi/bin"
    else:
        return f"{globals_variables.all_executions_dir}/pulumi-bin"


def execute_zenoh_routers(roles_zenoh_router, timeout, environment):
    log_experiment.log.debug(f"launch zenoh routers with {timeout} timeout")
    concerto_d_projects_dir = globals_variables.all_executions_dir if environment in ["remote", "raspberry"] else globals_variables.all_expes_dir  # TODO condition inutile

    # Need to specify the dirs to search libs (/usr/lib by default)
    zenoh_install_dir = _get_zenoh_install_dir()
    launch_router_cmd = " ".join(["timeout", str(timeout), f"{zenoh_install_dir}/zenohd", "-c", f"{zenoh_install_dir}/zenohd-config.json5", "--cfg", f"'plugins_search_dirs:[\"{zenoh_install_dir}\"]'"])
    kill_previous_routers_cmd = "kill $(ps -ef | grep -v grep | grep -w '" + zenoh_install_dir + "/zenohd -c " + zenoh_install_dir + "/zenohd-config.json5' | awk '{print $2}')"

    if environment in ["remote", "raspberry"]:
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
    src = f"{globals_variables.current_execution_dir}/{build_finished_reconfiguration_path(assembly_name, dep_num)}"
    dst = f"{globals_variables.current_expe_dir}/{build_finished_reconfiguration_path(assembly_name, dep_num)}"
    if environment in ["remote", "raspberry"]:
        with en.actions(roles=role_node) as a:
            a.fetch(src=src, dest=dst, flat="yes", fail_on_missing="no")
    else:
        if exists(src):
            os.makedirs(f"{globals_variables.current_expe_dir}/finished_reconfigurations", exist_ok=True)
            shutil.copy(src, dst)


def build_times_log_path(assembly_name, dep_num, timestamp_log_file: str):
    # return f"{assembly_name}_{timestamp_log_file}.yaml"
    if dep_num is None:
        return f"{assembly_name}_{timestamp_log_file}.yaml"
    else:
        return f"dep{dep_num}_{timestamp_log_file}.yaml"


def fetch_dir(roles, src_dir: str, dst_dir: str, environment):
    if environment in ["remote", "raspberry"]:
        for role in roles:
            with en.actions(roles=role) as a:
                a.find(paths=src_dir)

            for role_result in a.results:
                for file_item in role_result.payload["files"]:
                    src = file_item["path"]
                    file_name = src.split("/")[-1]
                    dest = f"{dst_dir}/{file_name}"

                    with en.actions(roles=role) as a:
                        a.fetch(src=src, dest=dest, flat="yes")

    else:
        os.makedirs(dst_dir, exist_ok=True)
        for file_path in os.listdir(src_dir):
            shutil.copy(f"{src_dir}/{file_path}", f"{dst_dir}/{file_path}")

# def fetch_times_log_files(roles, reconfiguration_name: str, environment):
#     dst_dir = f"{globals_variables.current_expe_dir}/logs_files_assemblies/{reconfiguration_name}"
#     with en.actions(roles=roles) as a:
#         a.find(paths=f"{globals_variables.current_execution_dir}/{reconfiguration_name}")
#     for file_item in a.results[0].payload["files"]:
#         file_name = file_item["path"].split("/")[-1]
#         dst = f"{dst_dir}/{file_name}"
#         _fetch_file(role_node, src, dst, dst_dir, environment)


def fetch_debug_log_files(role_node, assembly_type, dep_num, environment, use_case_name):
    if assembly_type == "server-clients":
        assembly_name = "server-clients"
    else:
        single_node_name = "server" if use_case_name == "parallel_deps" else "provider_node"
        linked_node_name = "dep" if use_case_name == "parallel_deps" else "chained_node"
        assembly_name = single_node_name if assembly_type == single_node_name else f"{linked_node_name}{dep_num}"
    file_name = f"logs_{assembly_name}.txt"
    dst_dir = f"{globals_variables.current_expe_dir}/logs_debug"
    src = f"{globals_variables.current_execution_dir}/logs/{file_name}"
    dst = f"{dst_dir}/{file_name}"
    _fetch_file(role_node, src, dst, dst_dir, environment)


def _fetch_file(role_node, src, dst, dst_dir, environment):
    os.makedirs(dst_dir, exist_ok=True)

    if environment in ["remote", "raspberry"]:
        process = subprocess.Popen(f"scp root@{role_node[0].address}:{src} {dst}", shell=True)
        exit_code = process.wait()
        if exit_code != 0:
            raise Exception(f"Error while fetch {role_node[0].address} (src: {src}, dst: {dst})")
    else:
        shutil.copy(src, dst)


def clean_previous_mjuz_environment(roles_concerto_d, environment):
    """
    Delete and recreate ~/.pulumi dir (containing state of deployed infrastructure) + kill all running
    ts-node processes
    """
    kill_ts_node_cmd = "kill -9 $(ps -aux | pgrep -f ts-node)"
    reset_pulumi_dir_cmd = f"rm -rf /tmp/.pulumi &&"
    trailing = ";" if environment in ["remote", "raspberry"] else ""
    reset_pulumi_dir_cmd += " PULUMI_SKIP_UPDATE_CHECK=1" + trailing
    reset_pulumi_dir_cmd += " PULUMI_AUTOMATION_API_SKIP_VERSION_CHECK=0" + trailing
    reset_pulumi_dir_cmd += f" {_get_pulumi_bin_path(environment)}/pulumi login file:///tmp"

    if environment in ["remote", "raspberry"]:
        en.run_command(kill_ts_node_cmd, roles=roles_concerto_d, on_error_continue=True)
        en.run_command(reset_pulumi_dir_cmd, roles=roles_concerto_d)

    else:
        subprocess.Popen(kill_ts_node_cmd, shell=True).wait()
        subprocess.Popen(reset_pulumi_dir_cmd, shell=True).wait()

