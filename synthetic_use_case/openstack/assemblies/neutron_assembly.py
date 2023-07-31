from concerto.assembly import Assembly
from synthetic_use_case.openstack.assemblies.neutron import Neutron


class NeutronAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, scaling_num):
        # L'ensemble assemblies présents sur les noeuds distants
        remote_assemblies = [f"mariadbworker{scaling_num}", f"keystone{scaling_num}"]

        # Le dict des types de composants utilisés au sein de l'assembly
        components_types = {
            "Neutron": Neutron
        }

        Assembly.__init__(
            self,
            f"neutron{scaling_num}",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
