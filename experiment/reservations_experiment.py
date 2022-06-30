import sys

from experiment import concerto_d_g5k


def get_normal_parameters():
    job_name_concerto = "concerto-d"
    job_name_controller = "controller"
    walltime = "08:30:00"
    reservation = "2022-06-26 16:00:00"
    nb_concerto_nodes = 13
    nb_zenoh_routers = 0
    return job_name_concerto, job_name_controller, walltime, reservation, nb_concerto_nodes, nb_zenoh_routers


def get_test_parameters():
    job_name_concerto = "concerto-d-test"
    job_name_controller = "controller-test"
    walltime = "01:00:00"
    reservation = None
    nb_concerto_nodes = 3
    nb_zenoh_routers = 1
    return job_name_concerto, job_name_controller, walltime, reservation, nb_concerto_nodes, nb_zenoh_routers


def main():
    # TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
    # Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
    # version specific de python-grid5000
    # TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
    is_normal = len(sys.argv) > 1 and sys.argv[1] == "normal"
    cluster = "uvb"
    if is_normal:
        job_name_concerto, job_name_controller, walltime, reservation, nb_concerto_nodes, nb_zenoh_routers = get_normal_parameters()
    else:
        job_name_concerto, job_name_controller, walltime, reservation, nb_concerto_nodes, nb_zenoh_routers = get_test_parameters()
    # walltime = "01:00:00"
    # reservation = "2022-06-26 16:00:00"
    # job_name_concerto_d = "concerto-d"
    # job_name_concerto_d_test = "concerto-d-test"
    # job_name_controller = "controller"
    # job_name_controller_test = "controller-test"
    # job_name_concerto = job_name_concerto_d_test if is_test else job_name_concerto_d
    # job_name_cont = job_name_controller_test if is_test else job_name_controller
    # nb_concerto_nodes = 2 if is_test else 13
    # nb_zenoh_routers = 0
    roles, networks = concerto_d_g5k.reserve_nodes_for_concerto_d(job_name_concerto, nb_concerto_d_nodes=nb_concerto_nodes, nb_zenoh_routers=nb_zenoh_routers, cluster=cluster, walltime=walltime, reservation=reservation)
    concerto_d_g5k.reserve_node_for_controller(job_name_controller, cluster, walltime=walltime, reservation=reservation)
    create_inventory_from_roles(roles)


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
