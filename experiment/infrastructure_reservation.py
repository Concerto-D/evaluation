import os
import sys
import traceback

import yaml

from experiment import concerto_d_g5k, experiment_controller, globals_variables, log_experiment, destroy_reservation


# Reservation experiment
# TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
# Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
# version specific de python-grid5000
# TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
from experiment import log_experiment


def create_reservation_for_concerto_d(version_concerto_d, reservation_parameters):
    (
        job_name_concerto,
        job_name_controller,
        walltime,
        reservation,
        nb_concerto_nodes,
        nb_zenoh_routers,
        cluster
    ) = reservation_parameters.values()
    log = log_experiment.log

    # Réservation nodes concerto_d, controller expé
    log.debug(f"Job should start at {reservation} and should last for {walltime}")
    log.debug(f"Reserve {nb_concerto_nodes} concerto_d and {nb_zenoh_routers} named {job_name_concerto}")
    roles_concerto_d, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name_concerto, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster, walltime=walltime, reservation=reservation)
    log.debug(f"Reserve the controller node named {job_name_controller}")
    # concerto_d_g5k.reserve_node_for_controller(job_name_controller, cluster, walltime=walltime, reservation=reservation)
    log.debug(f"reserved roles:")
    for k, v in roles_concerto_d.items():
        if k != "concerto_d":
            print(f"{k}: {v[0].address}")
    # Initialisation experiment repositories
    log.debug("Reserve the deployment node")
    deployment_node, networks, provider_deployment = concerto_d_g5k.reserve_node_for_controller("deployment", cluster, "00:10:00")
    log.debug("Initialise repositories")
    concerto_d_g5k.initialize_expe_repositories(deployment_node["controller"])
    if version_concerto_d == "synchronous":
        log.debug("Synchronous version: creating inventory")
        _create_inventory_from_roles(roles_concerto_d)  # TODO: put inventory on local dir
        log.debug("Put inventory file on frontend")
        concerto_d_g5k.put_file(deployment_node["controller"], "inventory.yaml", "concerto-decentralized/inventory.yaml")
    log.debug("Destroy deployment node")
    provider_deployment.destroy()

    return roles_concerto_d


def _create_inventory_from_roles(roles):
    with open("inventory.yaml", "w") as f:
        host = roles["server"][0].address
        f.write(f'server_assembly: "{host}:5000"')
        f.write("\n")
        f.write(f'server: "{host}:5000"')
        f.write("\n")
        for k, v in roles.items():
            if k not in ["server", "concerto_d", "zenoh_routers"]:
                dep_num = int(k.replace("dep", ""))
                port = 5001 + dep_num
                name_assembly = k.replace("dep", "dep_assembly_")
                f.write(f'{name_assembly}: "{v[0].address}:{port}"')
                f.write("\n")
                f.write(f'{k}: "{v[0].address}:{port}"')
                f.write("\n")
