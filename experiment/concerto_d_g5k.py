from typing import List, Optional

import enoslib as en
from enoslib.infra.enos_g5k.g5k_api_utils import get_cluster_site


def get_provider_from_job_name(job_name: str):
    conf = en.G5kConf.from_settings(job_name=job_name).finalize()
    return en.G5k(conf)


def reserve_node_for_deployment(cluster: str):
    # TODO: dire à Matthieu qu'il y a un problème entre enoslib et parasilo (le provider n'est pas reload alors que je donne le même job_name et le même cluster)
    _ = en.init_logging()
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


def reserve_node_for_controller(cluster: str, walltime: str = '01:00:00', reservation: Optional[str] = None):
    _ = en.init_logging()
    site = get_cluster_site(cluster)
    base_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime=walltime, reservation=reservation, job_name="controller")
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
    return roles, networks


def reserve_nodes_for_concerto_d(nb_concerto_d_nodes: int, nb_zenoh_routers: int, cluster: str, walltime: str = '01:00:00', reservation: Optional[str] = None):
    """
    TODO: voir pour les restriction des ressources (pour approcher des ressources d'une OU (raspberry ou autre))
    """
    _ = en.init_logging()
    site = get_cluster_site(cluster)
    concerto_d_network = en.G5kNetworkConf(type="prod", roles=["base_network"], site=site)
    # TODO: le walltime, le mettre jusqu'à 9am du jour d'après pour tous les noeuds
    # TODO: faire les réservations en avance pour toutes les expés (master + noeuds de l'expé), en amont dans un autre
    # script (voir aussi script Maverick + voir si on peut retrouver le provider depuis la conf).
    conf = (
        en.G5kConf.from_settings(job_type="allow_classic_ssh", walltime=walltime, reservation=reservation, job_name="concerto-d")
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
    roles = en.sync_info(roles, networks)

    netem = en.NetemHTB()
    netem.add_constraints(
        src=roles["zenoh_routers"],
        dest=roles[f"concerto_d"],
        delay="0ms",
        rate="200kbit",
        symetric=True,
    )
    netem.deploy()
    netem.validate()
    return roles, networks


def install_apt_deps(roles_concerto_d: List):
    with en.actions(roles=roles_concerto_d) as a:
        a.apt(name=["python3", "git"], state="present")
        print(a.results)


def put_assemblies_configuration_file(role_controller, configuration_file_path: str):
    with en.actions(roles=role_controller) as a:
        home_dir = "/home/anomond"
        a.copy(src=configuration_file_path, dest=f"{home_dir}/concertonode/{configuration_file_path}")
        print(a.results)


def put_uptimes_file(role_controller, uptimes_dir_path: str, uptimes_file_name: str):
    with en.actions(roles=role_controller) as a:
        home_dir = "/home/anomond"
        a.file(path=f"{home_dir}/concertonode/{uptimes_dir_path}", state="directory")
        a.copy(src=f"{uptimes_dir_path}/{uptimes_file_name}", dest=f"{home_dir}/concertonode/{uptimes_dir_path}/{uptimes_file_name}")
        print(a.results)


def initiate_concerto_d_dir(role_controller):
    """
    Homedir is shared between site frontend and nodes, so this can be done only once per site
    """
    with en.actions(roles=role_controller) as a:
        home_dir = "/home/anomond"
        a.copy(src="~/.ssh/gitlab_concerto_d_deploy_key", dest=f"{home_dir}/.ssh/gitlab_concerto_d_deploy_key")
        a.git(dest=f"{home_dir}/concertonode",
              repo="git@gitlab.inria.fr:aomond-imt/concerto-d/concerto-decentralized.git",
              key_file=f"{home_dir}/.ssh/gitlab_concerto_d_deploy_key",
              accept_hostkey=True)
        a.pip(chdir=f"{home_dir}/concertonode",
              requirements=f"{home_dir}/concertonode/requirements.txt",
              virtualenv=f"{home_dir}/concertonode/venv")
        a.file(path=f"{home_dir}/concertonode/evaluation/experiment/generated_covering_taux", state="directory")
        a.file(path=f"{home_dir}/concertonode/evaluation/experiment/generated_transitions_time", state="directory")
        a.file(path=f"{home_dir}/concertonode/evaluation/experiment/results_experiment", state="directory")
        a.file(path=f"{home_dir}/concertonode/evaluation/experiment/results_experiment/logs_files_assemblies", state="directory")
        # Reset reprise_configs dir
        a.file(path=f"{home_dir}/concertonode/concerto/reprise_configs", state="absent")
        a.file(path=f"{home_dir}/concertonode/concerto/reprise_configs", state="directory")
        # Reset logs dir
        a.file(path=f"{home_dir}/concertonode/concerto/logs", state="absent")
        a.file(path=f"{home_dir}/concertonode/concerto/logs", state="directory")
        a.file(path=f"{home_dir}/concertonode/concerto/archives_reprises", state="directory")
        # Reset finished_reconfigurations dir
        a.file(path=f"{home_dir}/concertonode/concerto/finished_reconfigurations", state="absent")
        a.file(path=f"{home_dir}/concertonode/concerto/finished_reconfigurations", state="directory")
        print(a.results)


def install_zenoh_router(roles_zenoh_router: List):
    with en.actions(roles=roles_zenoh_router) as a:
        a.apt_repository(repo="deb [trusted=yes] https://download.eclipse.org/zenoh/debian-repo/ /", state="present")
        a.apt(name="zenoh", update_cache="yes")
        print(a.results)


def execute_reconf(role_node, version_concerto_name, config_file_path: str, duration: float, timestamp_log_file: str, dep_num, experiment_num: int):
    command_args = []
    command_args.append(f"PYTHONPATH=$PYTHONPATH:$(pwd)/{version_concerto_name}")  # Set PYTHONPATH (equivalent of source source_dir.sh)
    command_args.append(f"{version_concerto_name}/venv/bin/python3")               # Execute inside the python virtualenv
    assembly_name = "server" if dep_num is None else "dep"
    command_args.append(f"evaluation/synthetic_use_case/reconf_programs/reconf_{assembly_name}.py")  # The reconf program to execute
    if dep_num is not None:
        command_args.append(str(dep_num))  # If it's a dependency
    command_args.append(config_file_path)  # The path of the config file that the remote process will search to
    command_args.append(str(duration))     # The awakening time of the program, it goes to sleep afterwards (it exits)
    command_args.append(str(experiment_num))
    command_args.append(timestamp_log_file)

    command_str = " ".join(command_args)
    home_dir = "/home/anomond"
    with en.actions(roles=role_node) as a:
        a.shell(chdir=f"{home_dir}/concertonode", command=command_str)


def execute_zenoh_routers(roles_zenoh_router, timeout):
    print(f"launch zenoh routers with {timeout} timeout")
    en.run_command("kill $(ps -ef | grep -v grep | grep -w zenohd | awk '{print $2}')", roles=roles_zenoh_router, on_error_continue=True)
    en.run_command(" ".join(["RUST_LOG=debug", "timeout", str(timeout), "zenohd", "--mem-storage='/**'"]), roles=roles_zenoh_router, background=True)


def build_finished_reconfiguration_path(assembly_name, dep_num):
    if dep_num is None:
        return f"finished_reconfigurations/{assembly_name}_assembly"
    else:
        return f"finished_reconfigurations/{assembly_name.replace(str(dep_num), '')}_assembly_{dep_num}"


def fetch_finished_reconfiguration_file(role_node, assembly_name, dep_num):
    home_dir = "/home/anomond"
    with en.actions(roles=role_node) as a:
        a.fetch(
            src=f"{home_dir}/concertonode/concerto/{build_finished_reconfiguration_path(assembly_name, dep_num)}",
            dest=f"concerto/{build_finished_reconfiguration_path(assembly_name, dep_num)}",
            flat="yes",
            fail_on_missing="no"
        )


def build_times_log_path(assembly_name, dep_num, timestamp_log_file: str):
    if dep_num is None:
        return f"{assembly_name}_{timestamp_log_file}.yaml"
    else:
        return f"dep{dep_num}_{timestamp_log_file}.yaml"


def fetch_times_log_file(role_node, assembly_name, dep_num, timestamp_log_file: str):
    with en.actions(roles=role_node) as a:
        a.fetch(
            src=f"/tmp/{build_times_log_path(assembly_name, dep_num, timestamp_log_file)}",
            dest=f"evaluation/experiment/results_experiment/logs_files_assemblies/{build_times_log_path(assembly_name, dep_num, timestamp_log_file)}",
            flat="yes"
        )


def get_logs_from_concerto_d_node(roles_sites, logs_assembly_names: List[str]):
    """
    Need one role per site to gather the logs
    """
    home_dir = "/home/anomond"
    with en.actions(roles=roles_sites) as a:
        for assembly_name in logs_assembly_names:
            a.fetch(src=f"{home_dir}/concertonode/concerto/logs/logs_{assembly_name}.txt", dest=f"concerto/remote_logs/logs_{assembly_name}.txt", flat="yes")
