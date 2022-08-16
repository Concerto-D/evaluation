import sys

import yaml

from experiment import concerto_d_g5k, execution_experiment, globals_variables, log_experiment

from evaluation.experiment import destroy_reservation


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
        log_experiment.initialize_logging(expe_name)
        roles, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name_concerto, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster, walltime=walltime, reservation=reservation)
        role_controller, _, _ = concerto_d_g5k.reserve_node_for_controller(job_name_controller, cluster, walltime=walltime, reservation=reservation)

        # Initialisation experiment
        cluster = "uvb"
        deployment_node, networks, provider_deployment = concerto_d_g5k.reserve_node_for_controller("controller", cluster)
        concerto_d_g5k.initialize_expe_repositories(deployment_node["controller"], version_concerto_d)
        if version_concerto_d == "concerto-decentralized-synchrone":
            create_inventory_from_roles(roles)
            concerto_d_g5k.put_file(deployment_node["controller"], "inventory.yaml", "concerto-decentralized-synchrone/inventory.yaml")

        provider_deployment.destroy()

        # Execution experiment
        params_to_sweep = parameters["sweeper_parameters"]
        execution_experiment.create_and_run_sweeper(expe_name, job_name_concerto, version_concerto_d, params_to_sweep, roles)

    except:
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
