from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model


class Heuristic:
    def __init__(self, model:Model, initial_node:HTNNode, name="blind"):
        self.model = model
        self.calls = 0
        self.total_hvalue = 0
        self.min_hvalue = 1000000
        self.initial_h = 0
        self.name = name
    
    
    def set_h_f_values(self, node:HTNNode, h_value, tie_breaking_values=[]):
        self.calls+=1
        self.total_hvalue+=h_value
        if self.min_hvalue > h_value:
            self.min_hvalue = h_value

        node.h_values[0] = h_value
        for h in tie_breaking_values:
            node.h_values.append(h)

        node.f_value = node.h_multiplier * node.h_values[0] + node.g_multiplier * node.g_value
        
    def __call__(self, parent_node, node):
        pass
    
    # when verbose
    def __output__(self):
        pass