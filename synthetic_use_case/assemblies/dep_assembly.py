from concerto.assembly import Assembly
from synthetic_use_case.assemblies.dep import Dep


class DepAssembly(Assembly):
    components_types = {
        "Dep": Dep
    }

    remote_component_names = {"server"}
    remote_assemblies_names = {"server_assembly"}

    def __init__(self, p, reconf_config_dict, sleep_when_blocked=True):
        Assembly.__init__(self, f"dep_assembly_{p}", self.components_types, self.remote_component_names,
                          self.remote_assemblies_names, reconf_config_dict, sleep_when_blocked)
        dep_params = reconf_config_dict['transitions_time'][f"dep{p}"]
        self.dep = Dep(**dep_params)

        # Adding remote components and assemblies
        for i in range(reconf_config_dict['nb_deps_tot']):
            if i != p:  # Not adding self
                self.remote_component_names.add(f"dep{i}")
                self.remote_assemblies_names.add(f"dep_assembly_{i}")
