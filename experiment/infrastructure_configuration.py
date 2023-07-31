from typing import Dict

import yaml
from enoslib import Host

from experiment import log_experiment, concerto_d_g5k, globals_variables


def configure_infrastructure(version_concerto_d: str, roles_concerto_d: Dict[str, Host], environment: str, use_case_name: str):
    log = log_experiment.log

    # Initialisation experiment repositories
    if environment in ["remote", "raspberry"]:
        log.debug("Initialise repositories")
        concerto_d_g5k.initialize_expe_repositories(version_concerto_d, roles_concerto_d["reconfiguring"])
        if version_concerto_d in ["mjuz", "mjuz-2-comps"]:
            concerto_d_g5k.initialize_deps_mjuz(roles_concerto_d["reconfiguring"], environment)

        if version_concerto_d in ["synchronous", "mjuz", "mjuz-2-comps"]:
            log.debug("Synchronous version: creating inventory")
            _create_inventory_from_roles(roles_concerto_d)


def _create_inventory_from_roles(roles):
    service_port = 5000
    inventory_as_dict = {}
    i = 0
    for comp_name, host in roles.items():
        if comp_name != "reconfiguring":
            inventory_as_dict[comp_name] = f"{host[0].address}:{service_port + i}"
            i += 2

    with open(globals_variables.inventory_name, "w") as f:
        yaml.safe_dump(inventory_as_dict, f, sort_keys=False)

    return inventory_as_dict


def test_create_inventory_from_roles():
    roles = {
        "mariadb_master": ["host1"],
        "mariadb0": ["host2"],
        "keystone0": ["host2"],
        "glance0": ["host2"],
        "nova0": ["host3"],
        "neutron0": ["host4"],
        "mariadb1": ["host5"],
        "keystone1": ["host5"],
        "glance1": ["host5"],
        "nova1": ["host6"],
        "neutron1": ["host7"],
    }

    r = _create_inventory_from_roles(roles)
    print()


if __name__ == "__main__":
    test_create_inventory_from_roles()
