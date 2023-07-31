from concerto.assembly import Assembly
from synthetic_use_case.openstack.assemblies.glance import Glance


class GlanceAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = [f"mariadbworker{scaling_num}", f"keystone{scaling_num}"]

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "Glance": Glance
        }

        Assembly.__init__(
            self,
            f"glance{scaling_num}",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
