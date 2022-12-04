from typing import Dict
from enoslib import Host

from experiment import log_experiment, concerto_d_g5k, globals_variables

CREATED_INVENTORY_PATH = "inventory.yaml"
CONCERTO_D_INVENTORY_PATH = "concerto-decentralized/inventory.yaml"
MJUZ_INVENTORY_PATH = "mjuz-concerto-d/inventory.yaml"


def configure_infrastructure(version_concerto_d: str, roles_concerto_d: Dict[str, Host], environment: str):
    log = log_experiment.log

    # Initialisation experiment repositories
    log.debug("Initialise repositories")
    concerto_d_g5k.initialize_expe_repositories(version_concerto_d, roles_concerto_d["server"])
    if version_concerto_d == "mjuz":
        concerto_d_g5k.initialize_deps_mjuz(roles_concerto_d["concerto_d"])

    if version_concerto_d in ["synchronous", "mjuz"]:
        log.debug("Synchronous version: creating inventory")
        _create_inventory_from_roles(roles_concerto_d)  # TODO: put inventory on local dir
        log.debug("Put inventory file on frontend")
        inventory_path = CONCERTO_D_INVENTORY_PATH if version_concerto_d == "synchronous" else MJUZ_INVENTORY_PATH
        if environment == "remote":
            inventory_path = f"/{inventory_path}"
        else:
            inventory_path = f"{globals_variables.all_executions_dir}/mjuz-concerto-d/{inventory_path}"
        concerto_d_g5k.put_file(roles_concerto_d, CREATED_INVENTORY_PATH, inventory_path)


def _create_inventory_from_roles(roles):
    with open(CREATED_INVENTORY_PATH, "w") as f:
        host = roles["server"][0].address
        f.write(f'server_assembly: "{host}:5000"')
        f.write("\n")
        f.write(f'server: "{host}:5000"')
        f.write("\n")
        for k, v in roles.items():
            if k not in ["server", "concerto_d", "zenoh_routers"]:
                dep_num = int(k.replace("dep", ""))
                port = 5001 + dep_num
                name_assembly = k.replace("dep", "dep_assembly_")
                f.write(f'{name_assembly}: "{v[0].address}:{port}"')
                f.write("\n")
                f.write(f'{k}: "{v[0].address}:{port}"')
                f.write("\n")
