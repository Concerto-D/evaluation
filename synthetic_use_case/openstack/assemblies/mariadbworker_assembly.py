from concerto.assembly import Assembly
from synthetic_use_case.openstack.assemblies.mariadbworker import MariadbWorker


class MariadbWorkerAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = ["mariadbmaster", f"keystone{scaling_num}", f"glance{scaling_num}", f"nova{scaling_num}", f"neutron{scaling_num}"]

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "MariadbWorker": MariadbWorker
        }

        Assembly.__init__(
            self,
            f"mariadbworker{scaling_num}",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
