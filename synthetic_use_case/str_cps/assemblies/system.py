import time

from concerto.component import Component
from concerto.dependency import DepType


class System(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "initiated",
            "configured",
            "deployed",
        ]
        self.groups = {
            "configured_group": ["configured", "deployed"]
        }

        self.transitions = {
            "initiate0": ("initiated", "configured", "deploy", 0, self.initiate0),
            "initiate1": ("initiated", "configured", "deploy", 0, self.initiate1),
            "initiate2": ("initiated", "configured", "deploy", 0, self.initiate2),
            "deploy": ("configured", "deployed", "deploy", 0, self.deploy),
            "stop": ("deployed", "initiated", "update", 0, self.stop),
        }
        self.dependencies = {
            "system_service_use": (DepType.USE, ["configured_group"]),
            "system_service_provide": (DepType.PROVIDE, ["deployed"])
        }

        self.initial_place = 'initiated'

    def initiate0(self):
        self.print_color("initiating0")
        time.sleep(self.trans_times["initiate0"])
        self.print_color("initiated0")

    def initiate1(self):
        self.print_color("initiating1")
        time.sleep(self.trans_times["initiate1"])
        self.print_color("initiated1")

    def initiate2(self):
        self.print_color("initiating2")
        time.sleep(self.trans_times["initiate2"])
        self.print_color("bootstrapped")

    def deploy(self):
        self.print_color("deploying")
        time.sleep(self.trans_times["deploy"])
        self.print_color("deployed")

    def stop(self):
        self.print_color("stopping")
        time.sleep(self.trans_times["stop"])
        self.print_color("stopped")
