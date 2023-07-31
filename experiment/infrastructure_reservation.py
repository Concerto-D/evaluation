from experiment import concerto_d_g5k
from enoslib import Host
from enoslib.objects import Roles


# Reservation experiment
# TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
# Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
# version specific de python-grid5000
# TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
from experiment import log_experiment


def create_infrastructure_reservation(expe_name, environment, reservation_params, use_case_nodes, version_concerto_d, use_case_name):
    log = log_experiment.log
    nodes = use_case_nodes[use_case_name]
    if environment == "remote":
        log.debug(f"Start {expe_name}")
        roles_concerto_d, provider = create_reservation_for_concerto_d(reservation_params, use_case_nodes, use_case_name, version_concerto_d)
    elif environment == "raspberry":
        roles_dict = {}
        if version_concerto_d == "central":
            server_client_host = Host("rpi-8.nantes.grid5000.fr", user="root")
            roles_concerto_d_list = [server_client_host]
            roles_dict["server-clients"] = [server_client_host]
        # elif version_concerto_d in ["synchronous", "asynchronous", "mjuz", "mjuz-2-comps"]:
        else:
            # TODO: refacto assembly_name
            server_host = Host("rpi-2.nantes.grid5000.fr", user="root")
            clients_hosts = [
                Host("rpi-3.nantes.grid5000.fr", user="root"),
                Host("rpi-4.nantes.grid5000.fr", user="root"),
                Host("rpi-6.nantes.grid5000.fr", user="root"),
                Host("rpi-7.nantes.grid5000.fr", user="root"),
                Host("rpi-8.nantes.grid5000.fr", user="root"),
            ]
            roles_concerto_d_list = [
                server_host
            ]
            roles_dict["server"] = [server_host]
            for dep_num in range(nodes["nb_dependencies"]):
                roles_dict[f"dep{dep_num}"] = [clients_hosts[dep_num]]
                roles_concerto_d_list.append(clients_hosts[dep_num])

            if version_concerto_d == "asynchronous":
                zenoh_router = Host("rpi-5.nantes.grid5000.fr", user="root")
                roles_dict["zenoh_routers"] = [zenoh_router]
        roles_dict["reconfiguring"] = roles_concerto_d_list
        roles_concerto_d = Roles(roles_dict)
        provider = None
    else:
        local_host = Host("localhost")
        if version_concerto_d == "central":
            nb_concerto_d_nodes = 1
        elif use_case_name == "parallel_deps":
            nb_concerto_d_nodes = nodes["nb_servers"] + nodes["nb_dependencies"]
        elif use_case_name in ["openstack", "str_cps"]:
            nb_concerto_d_nodes = 1 + 3*nodes["nb_scaled_sites"]
        else:
            nb_concerto_d_nodes = None

        roles_dict = {
            "reconfiguring": [local_host] * nb_concerto_d_nodes,
        }
        if version_concerto_d == "central":
            roles_dict.update({
                "server-clients": [local_host]
            })
        if version_concerto_d == "asynchronous":
            roles_dict.update({
                "zenoh_routers": [local_host]
            })
        if use_case_name == "parallel_deps":
            roles_dict.update({
                "server": [local_host],
                **{f"dep{dep_num}": [local_host] for dep_num in range(nodes["nb_dependencies"])},
            })
        if use_case_name == "openstack":
            # TODO: ajouter les autres éléments
            roles_dict.update(
                {"mariadbmaster": [local_host]}
            )
            for i in range(nodes["nb_scaled_sites"]):
                roles_dict.update(
                    {
                        f"nova{i}": [local_host],
                        f"neutron{i}": [local_host],
                    }
                )
                if "mjuz" in version_concerto_d:
                    roles_dict.update({f"worker{i}": [local_host]})
                else:
                    roles_dict.update({
                        f"keystone{i}": [local_host],
                        f"glance{i}": [local_host],
                        f"mariadbworker{i}": [local_host]
                    })
        if use_case_name == "str_cps":
            roles_dict.update({
                "database": [local_host], "system": [local_host]
            })
            for i in range(nodes["nb_scaled_sites"]):
                if "mjuz" in version_concerto_d:
                    roles_dict.update({f"cps{i}": [local_host]})
                else:
                    roles_dict.update({
                        f"listener{i}": [local_host], f"sensor{i}": [local_host]
                    })
        if use_case_name == "chained_deps":
            roles_dict.update({
                "provider_node": [local_host],
                **{f"chained_node{dep_num}": [local_host] for dep_num in range(nodes["nb_dependencies"])},
            })
        roles_concerto_d = Roles(roles_dict)
        provider = None

    return roles_concerto_d, provider


def create_reservation_for_concerto_d(reservation_parameters, use_case_nodes, use_case_name, version_concerto_d):
    (
        job_name_concerto,
        walltime,
        reservation,
        cluster,
        destroy_reservation
    ) = reservation_parameters.values()

    nodes = use_case_nodes[use_case_name]
    log = log_experiment.log

    # Réservation nodes concerto_d, controller expé
    log.debug(f"Reservation with the following parameters:")
    log.debug(f"job_name_concerto: {job_name_concerto}")
    log.debug(f"walltime: {walltime}")
    log.debug(f"reservation: {reservation}")
    log.debug(f"cluster: {cluster}")
    log.debug(f"use case nodes:")
    for key, val in nodes.items():
        log.debug(f"{key}: {val}")

    if use_case_name == "parallel_deps":
        roles_concerto_d, networks, provider = concerto_d_g5k.reserve_nodes_for_parallel_deps(
            job_name=job_name_concerto,
            nb_server_clients=nodes["nb_server_clients"],
            nb_servers=nodes["nb_servers"],
            nb_dependencies=nodes["nb_dependencies"],
            nb_zenoh_routers=nodes["nb_zenoh_routers"],
            cluster=cluster,
            walltime=walltime,
            reservation=reservation
        )
    elif use_case_name == "openstack":
        roles_concerto_d, networks, provider = concerto_d_g5k.reserve_nodes_for_openstack(
            job_name=job_name_concerto,
            nb_scaled_sites=nodes["nb_scaled_sites"],
            cluster=cluster,
            version_concerto_d=version_concerto_d,
            walltime=walltime,
            reservation=reservation
        )
    elif use_case_name == "str_cps":
        roles_concerto_d, networks, provider = concerto_d_g5k.reserve_nodes_for_cps_str(
            job_name=job_name_concerto,
            nb_scaled_sites=nodes["nb_scaled_sites"],
            cluster=cluster,
            version_concerto_d=version_concerto_d,
            walltime=walltime,
            reservation=reservation
        )
    else:
        roles_concerto_d, networks, provider = None, None, None
    concerto_d_g5k.add_host_keys_to_know_hosts(roles_concerto_d, cluster)
    log.debug(f"Reserved roles:")
    for k, v in roles_concerto_d.items():
        if k != "reconfiguring":
            log.debug(f"{k}: {v[0].address}")

    return roles_concerto_d, provider

