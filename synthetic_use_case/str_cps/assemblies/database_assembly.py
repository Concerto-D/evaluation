from concerto.assembly import Assembly
from synthetic_use_case.str_cps.assemblies.database import Database


class DatabaseAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = ["system"]

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "Database": Database
        }

        Assembly.__init__(
            self,
            "database",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
