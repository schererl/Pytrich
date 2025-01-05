
from Pytrich.Search.htn_node import TiebreakingNode


class Aggregation:
    def __init__(self, params):
        """
        Initializes the aggregation function with parsed parameters.
        The parameters can include heuristics or other aggregation functions.
        """
        self.params = params
    
    def initialize(self, model, node):
        pass
    
    def __output__(self):
        print(self.params)

class Max(Aggregation):
    def initialize(self, model, node):
        return max(param.initialize(model, node) for param in self.params)
    
    def __call__(self, parent_node, node):
        """
        Evaluate all parameters and return the maximum value.
        """
        # for param in self.params:
        #     print(f'name: {param} h: {param(parent_node,node)}', end=' ')
        # print()
        return max(param(parent_node, node) for param in self.params)

class Tiebreaking(Aggregation):
    def initialize(self, model, node):
        # print(f'initializing tie breakign')
        assert isinstance(node, TiebreakingNode)
        #for param in self.params:
            #print(f'initializing {param}')
            #param.initialize(model, node)

        values = tuple(param.initialize(model, node) for param in self.params)
        #print(values)
        return values
    
    def __call__(self, parent_node, node):
        """
        Evaluate all parameters and store their values for tie-breaking.
        """
        
        # for param in self.params:
        #     h= param(parent_node, node)
        #     print(f'{param}:{h}', end=' ')
        # print(f' ')
        
        return tuple(param(parent_node, node) for param in self.params)

