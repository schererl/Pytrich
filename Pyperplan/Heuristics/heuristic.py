from Pyperplan.Search.htn_node import HTNNode
from Pyperplan.model import Model


class Heuristic:
    def __init__(self, model:Model, initial_node:HTNNode, name="blind"):
        self.model = model
        self.calls = 0
        self.total_hvalue = 0
        self.min_hvalue = 1000000
        self.initial_h = 0
        self.name = name
    
    
    def set_h_f_values(self, node:HTNNode, h_value):
        self.calls+=1
        self.total_hvalue+=h_value
        if self.min_hvalue > h_value:
            self.min_hvalue = h_value
        node.h_value = h_value
        node.compute_f()
        
    def __call__(self, parent_node, node):
        pass
    
    # when verbose
    def __output__(self):
        pass