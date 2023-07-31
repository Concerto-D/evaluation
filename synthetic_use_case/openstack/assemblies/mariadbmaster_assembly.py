from concerto.assembly import Assembly
from synthetic_use_case.openstack.assemblies.mariadbmaster import MariadbMaster


class MariadbMasterAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = []
        for i in range(nb_concerto_nodes):
            remote_assemblies.append(f"mariadbworker{i}")

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "MariadbMaster": MariadbMaster
        }

        Assembly.__init__(
            self,
            "mariadbmaster",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
