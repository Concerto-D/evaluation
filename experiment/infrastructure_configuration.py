from typing import Dict
from enoslib import Host

from experiment import log_experiment, concerto_d_g5k, globals_variables


def configure_infrastructure(version_concerto_d: str, roles_concerto_d: Dict[str, Host], environment: str):
    log = log_experiment.log

    # Initialisation experiment repositories
    if environment in ["remote", "raspberry"]:
        log.debug("Initialise repositories")
        concerto_d_g5k.initialize_expe_repositories(version_concerto_d, roles_concerto_d["concerto_d"])
        if version_concerto_d in ["mjuz", "mjuz-2-comps"]:
            concerto_d_g5k.initialize_deps_mjuz(roles_concerto_d["concerto_d"], environment)

    if version_concerto_d in ["synchronous", "mjuz", "mjuz-2-comps"]:
        log.debug("Synchronous version: creating inventory")
        _create_inventory_from_roles(roles_concerto_d)


def _create_inventory_from_roles(roles):
    with open(globals_variables.inventory_name, "w") as f:
        host = roles["server"][0].address
        f.write(f'server_assembly: "{host}:5000"')
        f.write("\n")
        f.write(f'server: "{host}:5000"')
        f.write("\n")
        for k, v in roles.items():
            if k not in ["server", "concerto_d", "zenoh_routers", "server-clients"]:
                dep_num = int(k.replace("dep", ""))
                port = 5001 + dep_num
                name_assembly = k.replace("dep", "dep_assembly_")
                f.write(f'{name_assembly}: "{v[0].address}:{port}"')
                f.write("\n")
                f.write(f'{k}: "{v[0].address}:{port}"')
                f.write("\n")
