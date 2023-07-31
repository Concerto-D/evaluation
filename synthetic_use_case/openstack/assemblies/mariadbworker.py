import time

from concerto.component import Component
from concerto.dependency import DepType


class MariadbWorker(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "initiated",
            "configured",
            "bootstrapped",
            "restarted",
            "registered",
            "deployed",
            "interrupted"
        ]
        self.groups = {
            "bootstrapped_group": ["bootstrapped", "restarted", "registered", "deployed", "interrupted"]
        }

        self.transitions = {
            "configure0": ("initiated", "configured", "deploy", 0, self.configure0),
            "configure1": ("initiated", "configured", "deploy", 0, self.configure1),
            "bootstrap": ("configured", "bootstrapped", "deploy", 0, self.bootstrap),
            "start": ("bootstrapped", "restarted", "deploy", 0, self.start),
            "register": ("restarted", "registered", "deploy", 0, self.register),
            "deploy": ("registered", "deployed", "deploy", 0, self.deploy),
            "interrupt": ("deployed", "interrupted", "interrupt", 0, self.interrupt),
            "unconfigure": ("interrupted", "initiated", "update", 0, self.unconfigure),  # TODO: rename update in "uninstall" and correct the dependency name
        }
        self.dependencies = {
            "service": (DepType.PROVIDE, ["deployed"]),
            "master_service": (DepType.USE, ["bootstrapped_group"])
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
        self.print_color("bootstraping")
        time.sleep(self.trans_times["bootstrap"])
        self.print_color("bootstraped")

    def start(self):
        self.print_color("starting")
        time.sleep(self.trans_times["start"])
        self.print_color("started")

    def register(self):
        self.print_color("registering")
        time.sleep(self.trans_times["register"])
        self.print_color("registered")

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
