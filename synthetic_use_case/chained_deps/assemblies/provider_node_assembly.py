from concerto.assembly import Assembly
from synthetic_use_case.chained_deps.assemblies.provider_node import ProviderNode


class ProviderNodeAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
        remote_assemblies = {}

        components_types = {
            "ProviderNode": ProviderNode
        }

        Assembly.__init__(
            self,
            "provider_node_assembly",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
