from concerto.assembly import Assembly
from synthetic_use_case.assemblies.server import Server


class ServerAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d):
        # Add remote assemblies for the waitall instruction
        remote_assemblies_names = set()
        for i in range(reconf_config_dict['nb_deps_tot']):
            remote_assemblies_names.add(f"dep_assembly_{i}")

        # Add components types to instanciate for the add instruction
        components_types = {
            "Server": Server
        }

        Assembly.__init__(
            self,
            "server_assembly",
            components_types,
            remote_assemblies_names,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d
        )
