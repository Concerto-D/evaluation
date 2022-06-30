from experiment import concerto_d_g5k


def main():
    """
    Script d'initialisation à exécuter avant de lancer le controller d'expérience
    TODO: cannot find the same provider
    """
    cluster = "uvb"
    deployment_node, networks, provider = concerto_d_g5k.reserve_node_for_deployment(cluster)
    concerto_d_g5k.initiate_concerto_d_dir(deployment_node["deployment"])

    uptimes_dir_path_list = [
        ("experiment_files/parameters/uptimes/uptimes-30-30-2-0_98-1.json", "parameters/uptimes/uptimes-30-30-2-0_98-1.json"),
        ("experiment_files/parameters/uptimes/uptimes-30-30-12-0_2-0_3.json", "parameters/uptimes/uptimes-30-30-12-0_2-0_3.json"),
        ("experiment_files/parameters/uptimes/uptimes-30-30-12-0_02-0_05.json", "parameters/uptimes/uptimes-30-30-12-0_02-0_05.json"),
        ("experiment_files/parameters/uptimes/uptimes-30-30-12-0_5-0_6.json", "parameters/uptimes/uptimes-30-30-12-0_5-0_6.json"),
        ("experiment_files/parameters/transitions_times/mock_transitions_times-1-30-deps2.json", "parameters/transitions_times/mock_transitions_times-1-30-deps2.json"),
        ("experiment_files/parameters/transitions_times/transitions_times-1-30-deps12-0.json", "parameters/transitions_times/transitions_times-1-30-deps12-0.json"),
        ("experiment_files/parameters/transitions_times/transitions_times-1-30-deps12-1.json", "parameters/transitions_times/transitions_times-1-30-deps12-1.json"),
    ]
    for src, dst in uptimes_dir_path_list:
        concerto_d_g5k.put_uptimes_file(deployment_node["deployment"], src, dst)

    provider.destroy()


if __name__ == '__main__':
    main()
