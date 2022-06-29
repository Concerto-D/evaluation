from evaluation.experiment import concerto_d_g5k


def main():
    # TODO: mettre à jour le python-grid5000 avec verify_ssl pour autoriser les réservations depuis le front-end
    # Mettre à jour python-grid5000 n'a pas l'air d'être une bonne solution car la version d'enoslib utilise une
    # version specific de python-grid5000
    # TODO: à signaler: même avec verify_ssl ça ne suffit pas il faut mettre le user et le mdp sur le front-end
    cluster = "uvb"
    walltime = "10:00:00"
    reservation = "2022-06-26 16:00:00"
    concerto_d_g5k.reserve_nodes_for_concerto_d(nb_concerto_d_nodes=13, nb_zenoh_routers=1, cluster=cluster, walltime=walltime, reservation=reservation)
    concerto_d_g5k.reserve_node_for_controller(cluster, walltime=walltime, reservation=reservation)


if __name__ == '__main__':
    main()
