import time

from concerto.all import *
from examples.utils import *

class Dep(Component):

    def __init__(self, id : int = 0, t_di : float = 4.0, t_dr : float = 1.0, t_du : float = 3.0):
        self.my_ip = None
        self.id = id
        self.t_di = t_di
        self.t_dr = t_dr
        self.t_du = t_du
        Component.__init__(self)

    def create(self):
        self.places = [
            'undeployed',
            'installed',
            'running',
        ]

        self.transitions = {
            'install': ('undeployed', 'installed', 'deploy', 0, self.install),
            'run': ('installed', 'running', 'deploy', 0, self.run),
            'update': ('running', 'installed', 'update', 0, self.update)
        }

        self.dependencies = {
            'ip': (DepType.DATA_PROVIDE, ['installed']),
            'service': (DepType.PROVIDE, ['running'])
        }
        
        self.initial_place = 'undeployed'
        
    def display_name(self):
        return "Dep %d"%self.id

    def install(self):
        self.print_color("allocating resources")
        time.sleep(self.t_di)
        self.my_ip = "123.124.1.%d"% self.id
        self.print_color("got IP %s" % self.my_ip)
        self.write('ip', self.my_ip)
        self.print_color("finished allocation")

    def run(self):
        self.print_color("preparing to run")
        time.sleep(self.t_dr)
        self.print_color("running")

    def update(self):
        self.print_color("updating")
        time.sleep(self.t_du) 
        self.print_color("updated")
