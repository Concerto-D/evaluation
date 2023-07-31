import time

from concerto.component import Component
from concerto.dependency import DepType


class Database(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "initiated",
            "configured",
            "bootstrapped",
            "deployed",
            "registered",
        ]
        self.groups = {}

        self.transitions = {
            "configure0": ("initiated", "configured", "deploy", 0, self.configure0),
            "configure1": ("initiated", "configured", "deploy", 0, self.configure1),
            "bootstrap": ("configured", "bootstrapped", "deploy", 0, self.bootstrap),
            "deploy": ("bootstrapped", "deployed", "deploy", 0, self.deploy),
            "interrupt": ("deployed", "registered", "interrupt", 0, self.interrupt),
            "unconfigure": ("registered", "configured", "update", 0, self.unconfigure),
        }
        self.dependencies = {
            "database_service_provide": (DepType.PROVIDE, ["deployed"])
        }

        self.initial_place = 'initiated'

    def configure0(self):
        self.print_color("configuring0")
        time.sleep(self.trans_times["configure0"])
        self.print_color("configured0")

    def configure1(self):
        self.print_color("configuring1")
        time.sleep(self.trans_times["configure1"])
        self.print_color("configured1")

    def bootstrap(self):
        self.print_color("bootstrapping")
        time.sleep(self.trans_times["bootstrap"])
        self.print_color("bootstrapped")

    def deploy(self):
        self.print_color("deploying")
        time.sleep(self.trans_times["deploy"])
        self.print_color("deployed")

    def interrupt(self):
        self.print_color("interrupting")
        time.sleep(self.trans_times["interrupt"])
        self.print_color("interrupted")

    def unconfigure(self):
        self.print_color("unconfiguring")
        time.sleep(self.trans_times["unconfigure"])
        self.print_color("unconfigured")
