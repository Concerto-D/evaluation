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
            "server": Host("localhost"),
            **{f"dep{dep_num}": Host("localhost") for dep_num in range(reservation_params["nb_concerto_nodes"] - 1)},
            "zenoh_routers": Host("localhost")
        }
        provider = None

    return roles_concerto_d, provider


def create_reservation_for_concerto_d(reservation_parameters):
    (
        job_name_concerto,
        walltime,
        reservation,
        nb_concerto_nodes,
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
    log.debug(f"nb_concerto_nodes: {nb_concerto_nodes}")
    log.debug(f"nb_zenoh_routers: {nb_zenoh_routers}")
    log.debug(f"cluster: {cluster}")

    log.debug(f"Job should start at {reservation} and should last for {walltime}")
    log.debug(f"Reserve {nb_concerto_nodes} concerto_d and {nb_zenoh_routers} zenoh routers named {job_name_concerto}")
    roles_concerto_d, networks, provider = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name_concerto, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster, walltime=walltime, reservation=reservation)
    concerto_d_g5k.add_host_keys_to_know_hosts(roles_concerto_d, cluster)
    log.debug(f"Reserved roles:")
    for k, v in roles_concerto_d.items():
        if k != "concerto_d":
            log.debug(f"{k}: {v[0].address}")

    return roles_concerto_d, provider

