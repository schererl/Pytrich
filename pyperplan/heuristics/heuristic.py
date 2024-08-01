class Heuristic:
    def __init__(self, model, initial_node, name="blind"):
        self.model = model
        self.calls = 0
        self.total_hvalue = 0
        self.min_hvalue = 1000000
        self.initial_h = 0
        self.name = name
    
    def compute_heuristic(self, parent_node, node):
        pass

    def set_hvalue(self, node, h_value):
        self.calls+=1
        self.total_hvalue+=h_value
        if self.min_hvalue > h_value:
            self.min_hvalue = h_value
        node.h_value = h_value #TODO: satisficing for now
        node.f_value = h_value #node.g_value + h_value