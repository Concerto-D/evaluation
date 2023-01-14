import logging
import os
import sys
from datetime import datetime

from experiment import globals_variables

log = None


def initialize_logging(expe_name, stdout_only=False):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    experiment_results_dir = globals_variables.compute_current_expe_dir_from_name(expe_name)
    if not stdout_only:
        os.makedirs(f"{experiment_results_dir}/experiment_logs", exist_ok=True)
        logging.basicConfig(filename=f"{experiment_results_dir}/experiment_logs/experiment_logs_{timestamp}.txt", format='%(asctime)s %(message)s', filemode="a+")

    global log
    log = logging.getLogger(__name__)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    log.addHandler(console)
    log.setLevel(logging.DEBUG)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        log.debug("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
