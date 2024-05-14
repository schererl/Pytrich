import sys
from ..model import Operator
'''
NOTE: Im using Strategy pattern because I observe there is a significant difference
for searching time when we avoid 'if then else' selections, which in our case
was the '__lt__' function that changes when we are using a_star or not.
'''
class HTNNode:
    def __init__(self, parent, task, decomposition, state, task_network, seq_num, g_value):
        self.state = state
        self.parent = parent
        self.task = task
        self.decomposition = decomposition
        self.task_network = task_network
        self.seq_num = seq_num
        
        self.g_value = g_value
        self.f_value = 0
        self.h_value = 0

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
            if isinstance(self.task, Operator) and not "method_precondition" in self.task.name :
                operators.append(self.task)
            else:
                solution.append(self.decomposition)
            solution.append(self.task)
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


class AstarNode(HTNNode):
    def __lt__(self, other):
        if self.f_value ==  other.f_value:
            if self.h_value == other.h_value:
                return self.seq_num < other.seq_num
            return self.h_value < other.h_value
        return self.f_value < other.f_value
    
class AstarLMNode(HTNNode):
    def __init__(self, parent, task, decomposition, state, task_network, seq_num, g_value):
        super().__init__(parent, task, decomposition, state, task_network, seq_num, g_value)
        self.lm_node = None

    def __lt__(self, other):
        
        if self.f_value ==  other.f_value:
            if self.h_value == other.h_value:
                return self.seq_num < other.seq_num
            return self.h_value < other.h_value
        return self.f_value < other.f_value
    