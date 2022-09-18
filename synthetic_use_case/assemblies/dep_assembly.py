from concerto.assembly import Assembly
from synthetic_use_case.assemblies.dep import Dep


class DepAssembly(Assembly):
    def __init__(self, p, reconf_config_dict, waiting_rate, version_concerto_d):
        remote_assemblies_names = ["server_assembly"]

        # Adding remote components and assemblies
        for i in range(reconf_config_dict['nb_deps_tot']):
            if i != p:  # Not adding self
                remote_assemblies_names.append(f"dep_assembly_{i}")

        components_types = {
            "Dep": Dep
        }

        Assembly.__init__(
            self,
            f"dep_assembly_{p}",
            components_types,
            remote_assemblies_names,
            reconf_config_dict["transitions_times"],
            waiting_rate,
            version_concerto_d
        )
