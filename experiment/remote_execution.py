import sys

import enoslib as en
from enoslib.objects import Roles

if __name__ == "__main__":
    configuration_expe_file_path = sys.argv[1]
    role_frontend = Roles({"frontend": [en.Host("nantes.g5k")]})
    concerto_d_projects_dir = "/home/anomond/concerto_d_projects"
    print("Pull evaluation and experiment_files dirs")
    with en.actions(roles=role_frontend) as a:
        a.git(dest=f"{concerto_d_projects_dir}/evaluation",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/evaluation.git",
              version="main",
              accept_hostkey=True)
        a.git(dest=f"{concerto_d_projects_dir}/experiment_files",
              repo="https://gitlab.inria.fr/aomond-imt/concerto-d/experiment_files.git",
              accept_hostkey=True)
    print("done")
    print("Run expe inside tmux: exec_expe")
    en.run_command(
        f"tmux new-session -d -s exec_expe 'source ~/.bashrc && se && python3 experiment/execution_experiment.py ../{configuration_expe_file_path}'"
    )
    print("done")
