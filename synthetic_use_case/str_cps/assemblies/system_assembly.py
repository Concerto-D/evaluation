from concerto.assembly import Assembly
from synthetic_use_case.str_cps.assemblies.system import System


class SystemAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = ["database"]
        for i in range(nb_concerto_nodes):
            remote_assemblies.append(f"listener{i}")

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "System": System
        }

        Assembly.__init__(
            self,
            "system",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
