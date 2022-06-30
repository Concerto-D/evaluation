import logging
import os
from datetime import datetime

os.makedirs("experiment_logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logging.basicConfig(filename=f"experiment_logs/experiment_logs_{timestamp}.txt", format='%(asctime)s %(message)s', filemode="a+")
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
