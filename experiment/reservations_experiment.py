import sys
import traceback

import yaml

from experiment import concerto_d_g5k, execution_experiment, globals_variables, log_experiment, destroy_reservation


def main():
    # Reservation experiment
    # TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
    # Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
    # version specific de python-grid5000
    # TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
    configuration_file_path = sys.argv[1]

    cluster = "uvb"
    with open(configuration_file_path) as f:
        parameters = yaml.safe_load(f)
        expe_name, job_name_concerto, job_name_controller, walltime, reservation, nb_concerto_nodes, nb_zenoh_routers, version_concerto_d = parameters["reservation_parameters"].values()

    try:
        log = log_experiment.initialize_logging(expe_name)
        log.debug(f"Start {expe_name} for {version_concerto_d}")
        log.debug(f"Job should start at {reservation} and should last for {walltime}")
        log.debug(f"Reserve {nb_concerto_nodes} concerto_d and {nb_zenoh_routers} named {job_name_concerto}")
        roles, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name_concerto, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster, walltime=walltime, reservation=reservation)
        log.debug(f"Reserve the controller node named {job_name_controller}")
        role_controller, _, _ = concerto_d_g5k.reserve_node_for_controller(job_name_controller, cluster, walltime=walltime, reservation=reservation)

        # Initialisation experiment
        cluster = "uvb"
        log.debug("Reserve the deployment node")
        deployment_node, networks, provider_deployment = concerto_d_g5k.reserve_node_for_controller("deployment", cluster)
        log.debug("Initialise repositories")
        concerto_d_g5k.initialize_expe_repositories(deployment_node["deployment"], version_concerto_d)
        if version_concerto_d == "concerto-decentralized-synchrone":
            log.debug("Synchronous version: creating inventory")
            create_inventory_from_roles(roles)
            log.debug("Put inventory file on frontend")
            concerto_d_g5k.put_file(deployment_node["controller"], "inventory.yaml", "concerto-decentralized-synchrone/inventory.yaml")
        log.debug("Destroy deployment node")
        provider_deployment.destroy()
        # Execution experiment
        params_to_sweep = parameters["sweeper_parameters"]
        execution_experiment.create_and_run_sweeper(expe_name, job_name_concerto, version_concerto_d, params_to_sweep, roles)

    except:
        traceback.print_exc()
        if reservation == "":
            destroy_reservation.destroy_reservation(expe_name)


def create_inventory_from_roles(roles):
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


if __name__ == '__main__':
    main()
