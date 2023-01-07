from concerto.assembly import Assembly
from concerto.time_checker_assemblies import TimeCheckerAssemblies
from synthetic_use_case.assemblies.dep import Dep
from synthetic_use_case.assemblies.server import Server


class ServerClientsAssembly(Assembly):
    def __init__(self, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes, uptimes_nodes_file_path, execution_start_time):
        remote_assemblies = {}

        # Add components types to instanciate for the add instruction
        components_types = {
            "Server": Server,
            "Dep": Dep
        }
        Assembly.__init__(
            self,
            "server_clients_assembly",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name,
            uptimes_nodes_file_path
        )
