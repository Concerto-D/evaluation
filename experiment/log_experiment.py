import logging
import sys
from datetime import datetime

from experiment import globals_variables

log = None


def initialize_logging(expe_name):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    experiment_results_dir = globals_variables.experiment_results_dir(expe_name)
    logging.basicConfig(filename=f"{experiment_results_dir}/experiment_logs/experiment_logs_{timestamp}.txt", format='%(asctime)s %(message)s', filemode="a+")
    global log
    log = logging.getLogger(__name__)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    log.addHandler(console)
    log.setLevel(logging.DEBUG)
