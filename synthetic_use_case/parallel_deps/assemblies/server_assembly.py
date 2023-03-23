from concerto.assembly import Assembly
from synthetic_use_case.parallel_deps.assemblies.server import Server


class ServerAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
        # Add remote assemblies for the waitall instruction
        remote_assemblies = {}
        for i in range(nb_concerto_nodes):
            remote_assemblies[f"dep_assembly_{i}"] = f"dep{i}"

        # Add components types to instanciate for the add instruction
        components_types = {
            "Server": Server
        }

        Assembly.__init__(
            self,
            "server_assembly",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
