import time

from concerto.component import Component
from concerto.dependency import DepType


class Keystone(Component):
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
            "pull": ("initiated", "pulled", "deploy", 0, self.pull),
            "deploy": ("pulled", "deployed", "deploy", 0, self.deploy),
            "turnoff": ("deployed", "initiated", "stop", 0, self.turnoff),
        }
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "worker_service": (DepType.USE, ["pulled_group"]),
        }

        self.initial_place = 'initiated'

    def pull(self):
        self.print_color("pulling")
        time.sleep(self.trans_times["pull"])
        self.print_color("pulled")

    def deploy(self):
        self.print_color("deploying")
        time.sleep(self.trans_times["deploy"])
        self.print_color("deployed")

    def turnoff(self):
        self.print_color("turnoffing")
        time.sleep(self.trans_times["turnoff"])
        self.print_color("turnoffed")
