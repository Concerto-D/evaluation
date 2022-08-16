import sys

from experiment import concerto_d_g5k

if __name__ == "__main__":
    expe_name = sys.argv[1]
    job_name_concerto = f"concerto-d-{expe_name}"
    job_name_controller = f"controller-{expe_name}"
    concerto_d_g5k.destroy_provider_from_job_name(job_name_concerto)
    concerto_d_g5k.destroy_provider_from_job_name(job_name_controller)