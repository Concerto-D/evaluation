from concerto.assembly import Assembly
from synthetic_use_case.assemblies.dep import Dep


class DepAssembly(Assembly):
    def __init__(self, p, reconf_config_dict, waiting_rate, version_concerto_d, reconfiguration_name, nb_concerto_nodes):
        remote_assemblies = {"server_assembly": "server"}

        # Adding remote components and assemblies
        for i in range(nb_concerto_nodes):
            if i != p:  # Not adding self
                remote_assemblies[f"dep_assembly_{i}"] = f"dep{i}"

        components_types = {
            "Dep": Dep
        }

        Assembly.__init__(
            self,
            f"dep_assembly_{p}",
            components_types,
            remote_assemblies,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d,
            nb_concerto_nodes,
            reconfiguration_name
        )
