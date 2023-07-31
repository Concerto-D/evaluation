from concerto.assembly import Assembly
from synthetic_use_case.str_cps.assemblies.listener import Listener


class ListenerAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = ["system", f"sensor{scaling_num}"]

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "Listener": Listener
        }

        Assembly.__init__(
            self,
            f"listener{scaling_num}",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
