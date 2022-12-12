from experiment import concerto_d_g5k
from enoslib import Host


# Reservation experiment
# TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
# Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
# version specific de python-grid5000
# TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
from experiment import log_experiment


def create_infrastructure_reservation(expe_name, environment, reservation_params):
    log = log_experiment.log
    if environment == "remote":
        log.debug(f"Start {expe_name}")
        roles_concerto_d, provider = create_reservation_for_concerto_d(reservation_params)
    else:
        roles_concerto_d = {
            "server-clients": [Host("localhost")],
            "server": [Host("localhost")],
            **{f"dep{dep_num}": [Host("localhost")] for dep_num in range(reservation_params["nb_dependencies"])},
            "zenoh_routers": [Host("localhost")]
        }
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

