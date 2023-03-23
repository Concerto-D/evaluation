from concerto.component import Component


class ProviderNode(Component):
    def __init__(self):
        Component.__init__(self)

    def create(self):
        self.places = []
        self.transitions = {}
        self.dependencies = {}
        self.initial_place = 'undeployed'
