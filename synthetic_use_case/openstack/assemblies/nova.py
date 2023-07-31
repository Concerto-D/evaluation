import time

from concerto.component import Component
from concerto.dependency import DepType


class Nova(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "initiated",
            "pulled",
            "ready",
            "restarted",
            "deployed",
            "interrupted"
        ]
        self.groups = {
            "pulled_group": ["pulled", "ready", "restarted", "deployed"],
            "ready_group": ["ready", "restarted", "deployed"],
        }

        self.transitions = {
            "pull0": ("initiated", "pulled", "deploy", 0, self.pull0),
            "pull1": ("initiated", "pulled", "deploy", 0, self.pull1),
            "pull2": ("initiated", "pulled", "deploy", 0, self.pull2),
            "ready0": ("pulled", "ready", "deploy", 0, self.ready0),
            "ready1": ("pulled", "ready", "deploy", 0, self.ready1),
            "start": ("ready", "restarted", "deploy", 0, self.start),
            "deploy": ("restarted", "deployed", "deploy", 0, self.deploy),
            "cell_setup": ("pulled", "deployed", "deploy", 0, self.cell_setup),
            "interrupt": ("deployed", "interrupted", "interrupt", 0, self.interrupt),
            "unpull": ("interrupted", "pulled", "update", 0, self.unpull),
        }
        self.dependencies = {
            "mariadbworker_service": (DepType.USE, ["pulled_group"]),
            "keystone_service": (DepType.USE, ["ready_group"]),
        }

        self.initial_place = 'initiated'

    def pull0(self):
        self.print_color("pulling0")
        time.sleep(self.trans_times["pull0"])
        self.print_color("pulled0")

    def pull1(self):
        self.print_color("pulling1")
        time.sleep(self.trans_times["pull1"])
        self.print_color("pulled1")

    def pull2(self):
        self.print_color("pulling2")
        time.sleep(self.trans_times["pull2"])
        self.print_color("pulled2")

    def ready0(self):
        self.print_color("readying0")
        time.sleep(self.trans_times["ready0"])
        self.print_color("readyed0")

    def ready1(self):
        self.print_color("readying1")
        time.sleep(self.trans_times["ready1"])
        self.print_color("readyed1")

    def start(self):
        self.print_color("starting")
        time.sleep(self.trans_times["start"])
        self.print_color("started")

    def deploy(self):
        self.print_color("deploying")
        time.sleep(self.trans_times["deploy"])
        self.print_color("deployed")

    def cell_setup(self):
        self.print_color("cell_setuping")
        time.sleep(self.trans_times["cell_setup"])
        self.print_color("cell_setuped")

    def interrupt(self):
        self.print_color("interrupting")
        time.sleep(self.trans_times["interrupt"])
        self.print_color("interrupted")

    def unpull(self):
        self.print_color("unpulling")
        time.sleep(self.trans_times["unpull"])
        self.print_color("unpulled")
