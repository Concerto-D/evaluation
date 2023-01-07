from experiment import concerto_d_g5k
from enoslib import Host
from enoslib.objects import Roles


# Reservation experiment
# TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
# Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
# version specific de python-grid5000
# TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
from experiment import log_experiment


def create_infrastructure_reservation(expe_name, environment, reservation_params, version_concerto_d):
    log = log_experiment.log
    if environment == "remote":
        log.debug(f"Start {expe_name}")
        roles_concerto_d, provider = create_reservation_for_concerto_d(reservation_params)
    elif environment == "raspberry":
        roles_dict = {}
        if version_concerto_d == "central":
            server_client_host = Host("rpi-8.nantes.grid5000.fr", user="root")
            roles_concerto_d_list = [server_client_host]
            roles_dict["server-clients"] = [server_client_host]
        # elif version_concerto_d in ["synchronous", "asynchronous", "mjuz", "mjuz-2-comps"]:
        else:
            server_host = Host("rpi-8.nantes.grid5000.fr", user="root")
            clients_hosts = [
                Host("rpi-7.nantes.grid5000.fr", user="root"),
                Host("rpi-6.nantes.grid5000.fr", user="root"),
            ]
            roles_concerto_d_list = [
                server_host,
                *clients_hosts
            ]
            roles_dict["server"] = [server_host]
            for dep_num in range(reservation_params["nb_dependencies"]):
                roles_dict[f"dep{dep_num}"] = [clients_hosts[dep_num]]

            if version_concerto_d == "asynchronous":
                zenoh_router = Host("rpi-5.nantes.grid5000.fr", user="root")
                roles_dict["zenoh_routers"] = [zenoh_router]
        roles_dict["concerto_d"] = roles_concerto_d_list
        roles_concerto_d = Roles(roles_dict)
        provider = None
    else:
        local_host = Host("localhost")
        nb_concerto_d_nodes = 1 if reservation_params["nb_server_clients"] == 1 else 13
        roles_concerto_d = Roles({
            "server-clients": [local_host],
            "server": [local_host],
            **{f"dep{dep_num}": [local_host] for dep_num in range(reservation_params["nb_dependencies"])},
            "concerto_d": [local_host] * nb_concerto_d_nodes,
            "zenoh_routers": [local_host]
        })
        provider = None

    return roles_concerto_d, provider


def create_reservation_for_concerto_d(reservation_parameters):
    (
        job_name_concerto,
        walltime,
        reservation,
        nb_server_clients,
        nb_servers,
        nb_dependencies,
        nb_zenoh_routers,
        cluster,
        destroy_reservation
    ) = reservation_parameters.values()
    log = log_experiment.log

    # Réservation nodes concerto_d, controller expé
    log.debug(f"Reservation with the following parameters:")
    log.debug(f"job_name_concerto: {job_name_concerto}")
    log.debug(f"walltime: {walltime}")
    log.debug(f"reservation: {reservation}")
    log.debug(f"nb_server_clients: {nb_server_clients}")
    log.debug(f"nb_servers: {nb_servers}")
    log.debug(f"nb_dependencies: {nb_dependencies}")
    log.debug(f"nb_zenoh_routers: {nb_zenoh_routers}")
    log.debug(f"cluster: {cluster}")

    roles_concerto_d, networks, provider = concerto_d_g5k.reserve_nodes_for_concerto_d(
        job_name=job_name_concerto,
        nb_server_clients=nb_server_clients,
        nb_servers=nb_servers,
        nb_dependencies=nb_dependencies,
        nb_zenoh_routers=nb_zenoh_routers,
        cluster=cluster,
        walltime=walltime,
        reservation=reservation
    )
    concerto_d_g5k.add_host_keys_to_know_hosts(roles_concerto_d, cluster)
    log.debug(f"Reserved roles:")
    for k, v in roles_concerto_d.items():
        if k != "concerto_d":
            log.debug(f"{k}: {v[0].address}")

    return roles_concerto_d, provider

