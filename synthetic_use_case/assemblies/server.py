from concerto.all import *

class Server(Component):

    def __init__(self, t_sa : float, t_sc : List[float], t_sr : float, t_ss : List[float], t_sp : List[float], nb_deps: int):
        self.nb_deps = nb_deps
        self.t_sa = t_sa
        self.t_sc = t_sc
        self.t_sr = t_sr
        self.t_ss = t_ss
        self.t_sp = t_sp
        self.my_ip = None
        Component.__init__(self)

    def create(self):
        self.places = [
            'undeployed',
            'allocated',
            'configured',
            'running',
            'suspended'
        ]
        
        self.groups = {
        }

        self.transitions = {
            'allocate': ('undeployed', 'allocated', 'deploy', 0, self.allocate),
            'run': ('configured', 'running', 'deploy', 0, self.run)
        }

        self.dependencies = {
            'ip': (DepType.DATA_PROVIDE, ['allocated']),
            'service': (DepType.PROVIDE, ['running'])
        }
        
        for i in range(self.nb_deps):
            self.places.append(self.name_for_dep_suspended(i))
            self.groups[self.name_for_dep_group(i)] = ['running', self.name_for_dep_suspended(i)]
            self.transitions[self.name_for_dep_config(i)] = ('allocated', 'configured', 'deploy', 0, self.configure, [i])
            self.transitions[self.name_for_dep_suspend(i)] = ('running', self.name_for_dep_suspended(i), 'suspend', 0, self.suspend, [i])
            self.transitions[self.name_for_dep_prepare(i)] = (self.name_for_dep_suspended(i), 'configured', 'suspend', 0, self.prepare, [i])
            self.dependencies[self.name_for_dep_ip(i)] = (DepType.DATA_USE, [self.name_for_dep_config(i)])
            self.dependencies[self.name_for_dep_service(i)] = (DepType.USE, [self.name_for_dep_group(i)])
        
        self.initial_place = 'undeployed'
        
    @staticmethod
    def name_for_dep_suspended(i : int):
        return "suspended%d"%i
    @staticmethod
    def name_for_dep_group(i : int):
        return "group%d"%i
    @staticmethod
    def name_for_dep_config(i : int):
        return "config%d"%i
    @staticmethod
    def name_for_dep_suspend(i : int):
        return "suspend%d"%i
    @staticmethod
    def name_for_dep_prepare(i : int):
        return "prepare%d"%i
    @staticmethod
    def name_for_dep_ip(i : int):
        return "serviceu_ip%d"%i
    @staticmethod
    def name_for_dep_service(i : int):
        return "serviceu%d"%i

    def allocate(self):
        self.print_color("allocating resources")
        time.sleep(self.t_sa)
        self.my_ip = "123.124.1.2"
        self.write('ip', self.my_ip)
        self.print_color("finished allocation (ip:%s)"%self.my_ip)
        
    def configure(self, dependency_id : int):
        self.print_color("waiting for dependency %d"%dependency_id)
        time.sleep(self.t_sc[dependency_id])
        self.print_color("dependency %d configured"%dependency_id)

    def run(self):
        self.print_color("preparing to run")
        time.sleep(self.t_sr)
        self.print_color("running")

    def suspend(self, dependency_id : int):
        self.print_color("suspending dependency %d"%dependency_id)
        time.sleep(self.t_ss[dependency_id])
        self.print_color("suspended dependency %d"%dependency_id)

    def prepare(self, dependency_id : int):
        self.print_color("preparing dependency %d"%dependency_id)
        time.sleep(self.t_sp[dependency_id])
        self.print_color("prepared dependency %d"%dependency_id)
