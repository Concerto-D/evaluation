from experiment import concerto_d_g5k


def main():
    """
    Script d'initialisation à exécuter avant de lancer le controller d'expérience
    TODO: cannot find the same provider
    """
    cluster = "uvb"
    deployment_node, networks, provider = concerto_d_g5k.reserve_node_for_deployment(cluster)
    concerto_d_g5k.initiate_concerto_d_dir(deployment_node["deployment"])

    uptimes_dir_path = "evaluation/experiment/generated_covering_taux/2022-06-26_14-50-58"
    uptimes_file_name = "uptimes.json"
    concerto_d_g5k.put_uptimes_file(deployment_node["deployment"], uptimes_dir_path, uptimes_file_name)
    provider.destroy()


if __name__ == '__main__':
    main()
