import time

from concerto.component import Component
from concerto.dependency import DepType


class Glance(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "initiated",
            "pulled",
            "deployed",
        ]
        self.groups = {
            "pulled_group": ["pulled", "deployed"]
        }

        self.transitions = {
            "pull0": ("initiated", "pulled", "deploy", 0, self.pull0),
            "pull1": ("initiated", "pulled", "deploy", 0, self.pull1),
            "pull2": ("initiated", "pulled", "deploy", 0, self.pull2),
            "deploy": ("pulled", "deployed", "deploy", 0, self.deploy),
            "turnoff": ("deployed", "initiated", "uninstall", 0, self.turnoff),
        }
        self.dependencies = {
            "worker_service": (DepType.USE, ["pulled_group"]),
            "keystone_service": (DepType.USE, ["pulled_group"]),
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

    def deploy(self):
        self.print_color("deploying")
        time.sleep(self.trans_times["deploy"])
        self.print_color("deployed")

    def turnoff(self):
        self.print_color("turnoffing")
        time.sleep(self.trans_times["turnoff"])
        self.print_color("turnoffed")
