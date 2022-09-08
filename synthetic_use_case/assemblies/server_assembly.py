from concerto.assembly import Assembly
from synthetic_use_case.assemblies.server import Server


class ServerAssembly(Assembly):
    components_types = {
        "Server": Server
    }

    remote_component_names = set()   # Filled on __init__
    remote_assemblies_names = set()  # Filled on __init__

    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d):
        Assembly.__init__(self, "server_assembly", self.components_types, self.remote_component_names,
                          self.remote_assemblies_names, reconf_config_dict, waiting_rate, version_concerto_d)
        server_params = reconf_config_dict['transitions_time']['server']
        self.server = Server(nb_deps=reconf_config_dict['nb_deps_tot'], **server_params)

        # Adding remote components and assemblies
        for i in range(reconf_config_dict['nb_deps_tot']):
            self.remote_component_names.add(f"dep{i}")
            self.remote_assemblies_names.add(f"dep_assembly_{i}")