import time

from concerto.component import Component
from concerto.dependency import DepType


class Sensor(Component):
    def __init__(self, **kwargs):
        Component.__init__(self)
        self.trans_times = kwargs

    def create(self):
        self.places = [
            "off",
            "provisionned",
            "installed",
            "configured",
            "running",
        ]
        self.groups = {
            "installed_group": ["installed", "configured"],
            "configured_group": ["configured", "running"],
        }

        self.transitions = {
            "provision0": ("off", "provisionned", "deploy", 0, self.provision0),
            "provision1": ("off", "provisionned", "deploy", 0, self.provision1),
            "provision2": ("off", "provisionned", "deploy", 0, self.provision2),
            "install": ("provisionned", "installed", "deploy", 0, self.install),
            "configure": ("installed", "configured", "deploy", 0, self.configure),
            "run": ("configured", "running", "deploy", 0, self.run),
            "pause": ("running", "provisionned", "pause", 0, self.pause),
        }
        self.dependencies = {
            "sensor_config_use": (DepType.USE, ["installed_group"]),
            "sensor_service_use": (DepType.USE, ["configured_group"])
        }

        self.initial_place = 'off'

    def provision0(self):
        self.print_color("provisionning0")
        time.sleep(self.trans_times["provision0"])
        self.print_color("provisionned0")

    def provision1(self):
        self.print_color("provisionning1")
        time.sleep(self.trans_times["provision1"])
        self.print_color("provisionned1")

    def provision2(self):
        self.print_color("provisionning2")
        time.sleep(self.trans_times["provision2"])
        self.print_color("provisionned2")

    def install(self):
        self.print_color("installing")
        time.sleep(self.trans_times["install"])
        self.print_color("installed")

    def configure(self):
        self.print_color("configuring")
        time.sleep(self.trans_times["configure"])
        self.print_color("configured")

    def run(self):
        self.print_color("running")
        time.sleep(self.trans_times["run"])
        self.print_color("runned")

    def pause(self):
        self.print_color("pausing")
        time.sleep(self.trans_times["pause"])
        self.print_color("paused")

