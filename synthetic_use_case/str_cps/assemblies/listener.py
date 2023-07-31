import time

from concerto.component import Component
from concerto.dependency import DepType


class Listener(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "off",
            "paused",
            "configured",
            "running",
        ]
        self.groups = {
            "configured_group": ["configured", "running"]
        }

        self.transitions = {
            "start": ("off", "paused", "deploy", 0, self.start),
            "configure": ("paused", "configured", "deploy", 0, self.configure),
            "run": ("configured", "running", "deploy", 0, self.run),
            "interrupt": ("running", "paused", "update", 0, self.interrupt),
        }
        self.dependencies = {
            "listener_service_use": (DepType.USE, ["configured_group"]),
            "listener_config_provide": (DepType.PROVIDE, ["configured_group"]),
            "listener_service_provide": (DepType.PROVIDE, ["running"])
        }

        self.initial_place = 'off'

    def start(self):
        self.print_color("starting")
        time.sleep(self.trans_times["start"])
        self.print_color("started")

    def configure(self):
        self.print_color("configuring1")
        time.sleep(self.trans_times["configure"])
        self.print_color("configured1")

    def run(self):
        self.print_color("running")
        time.sleep(self.trans_times["run"])
        self.print_color("runned")

    def interrupt(self):
        self.print_color("interrupting")
        time.sleep(self.trans_times["interrupt"])
        self.print_color("interrupted")

