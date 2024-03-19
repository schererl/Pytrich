import sys
from ..model import Operator
'''
NOTE: Im using Strategy pattern because I observe there is a significant difference
for searching time when we avoid 'if then else' selections, which in our case
was the '__lt__' function that changes when we are using a_star or not.

Moreover, also makes a considerable difference when we avoid function calls, so we only
define the __lt__ function, without creating new __init__ functions and 'super()'
calls...
'''
class HTNNode:
    def __init__(self, parent, action, state, task_network, seq_num, g_value, h_val):
        self.state = state
        self.parent = parent
        self.action = action
        self.task_network = task_network
        self.seq_num = seq_num
        self.h_val = h_val
        self.g_value = g_value
        self.f_value = h_val + g_value

        self.ref_idx = 0
        # NOTE: only use if we search considering visited nodes -high computational cost
        self.hash_node = hash((self.state, tuple(task_network)))
    
    def extract_solution(self):
        """
        Returns the list of actions that were applied from the initial node to
        the goal node.
        """
        solution = []
        operators = []
        while self.parent is not None:
            if isinstance(self.action, Operator) and not "method_precondition" in self.action.name :
                operators.append(self.action)
            solution.append(self.action)
            self = self.parent
        solution.reverse()
        return solution, operators

    #TODO: not sure if im doing it right
    def __hash__(self):
        return self.hash_node
        
        
    def __eq__(self, other):
        return self.state == other.state and self.task_network == other.task_network

    def __str__(self):
        if type(self.state) == int:
            state_str = ''
        else:    
            state_str = '[\n\t\t' + '\n\t\t'.join(self.state)
        state_str=f'--- {self.seq_num}'
        memory_info = (
            f"\n\tMemory Usage:"
            f"\n\t\tState: {sys.getsizeof(self.state)} bytes"
            f"\n\t\tParent: {sys.getsizeof(self.parent)} bytes"
            f"\n\t\tAction: {sys.getsizeof(self.action)} bytes"
            f"\n\t\tTask Network: {sys.getsizeof(self.task_network)} bytes"
        )
        return (
            f"HTNNode: \n\tState: {{{state_str}}}"
            # f"\n\tAction: {self.action}"
            f"\n\tTaskNetwork: {self.task_network[0:min(5, len(self.task_network))]}"
            f"\n{memory_info}"
        )


#NOTE: Trying to figure out why using self.seq_num '<' other.seq_num instead of '>' increases 2x nodes/sec
class AstarNode(HTNNode):
    def __lt__(self, other):
        if self.f_value ==  other.f_value:
            if self.h_val == other.h_val:
                return self.seq_num < other.seq_num
            return self.h_val < other.h_val
        return self.f_value < other.f_value
    