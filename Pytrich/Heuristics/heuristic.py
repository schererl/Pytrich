from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model
class Heuristic:
    def __init__(self, name="blind"):
        self.model = None
        self.name = name
        self.calls = 0
        self.total_hvalue = 0
        self.min_hvalue = 1000000
        self.initial_h  = 0
    
    def initialize(self, model, initial_h):
        self.model=model
        self.initial_h=initial_h
        self.update_info(initial_h)
        return initial_h

    def update_info(self, h_value):
        """
        Set heuristic and f-value for the node.
        """
        self.calls += 1
        self.total_hvalue += h_value
        self.min_hvalue = min(self.min_hvalue, h_value)
        
    def __call__(self, parent_node, node):
        pass
    
    def __output__(self):
        pass