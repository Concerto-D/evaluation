import os
import sys
import tarfile

import enoslib as en
from enoslib.objects import Roles

from experiment import execution_experiment

configuration_expe_file_path = sys.argv[1]
global_params, reservation_params, email_parameters, sweeper_params = execution_experiment.extract_parameters(configuration_expe_file_path)

# Extract parametres globaux
(
    expe_name,
    environment,
    version_concerto_d,
    all_expes_dir,
    all_executions_dir,
    fetch_experiment_results,
    local_expe_res_dir,
    send_mail_after_all_expes
) = global_params.values()

role_frontend = Roles({"frontend": [en.Host("nantes.g5k")]})
g5k_site = "nantes"
local_expe_res_dir_root = "/home/aomond/experiments_results"
remote_expe_res_dir_root = "/home/anomond/experiments_results"

src_dir = f"{remote_expe_res_dir_root}/{expe_name}"
dst_dir = f"{local_expe_res_dir_root}/{local_expe_res_dir}"
tar_file = f"{remote_expe_res_dir_root}/{expe_name}.tar"

print(
    f"src_dir: {src_dir}",
    f"dst_dir: {dst_dir}",
    f"remote_tar_file: {tar_file}"
)

# TODO: check if file exists first
with en.actions(roles=role_frontend) as a:
    a.archive(
        path=src_dir,
        dest=tar_file
    )
    a.fetch(
        src=tar_file,
        dest=f"{local_expe_res_dir_root}/",
        flat="yes",
        fail_on_missing="no"
    )

os.makedirs(dst_dir, exist_ok=True)
with tarfile.open(f"{local_expe_res_dir_root}/{expe_name}.tar", "r") as tar:
    tar.extractall(dst_dir)

print(f"Extracted tar: {dst_dir}")
