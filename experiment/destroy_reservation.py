import sys

import yaml

from experiment import concerto_d_g5k


def destroy_reservation(parameters):
    concerto_d_g5k.destroy_provider_from_job_name(parameters["reservation_parameters"]["job_name_concerto"])


if __name__ == "__main__":
    configuration_file_path = sys.argv[1]
    with open(configuration_file_path) as f:
        parameters = yaml.safe_load(f)
    destroy_reservation(parameters)
