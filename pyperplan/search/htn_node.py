import sys

'''
NOTE: Im using Strategy pattern because I observe there is a significant difference
for searching time when we avoid 'if then else' selections, which in our case
was the '__lt__' function that changes when we are using a_star or not.

Moreover, also makes a considerable difference when we avoid function calls, so we only
define the __lt__ function, without creating new __init__ functions and 'super()'
calls...
'''
class HTNNode:
    def __init__(self, parent, action, state, task_network, seq_num, g_value, heuristic):
        self.state = state
        self.parent = parent
        self.action = action
        self.task_network = task_network
        self.seq_num = seq_num
        self.heuristic = heuristic
        self.g_value = g_value

        # NOTE: only use if we search considering visited nodes -high computational cost
        #self.hash_node = hash((self.state, tuple(task_network)))
    
    def extract_solution(self):
        """
        Returns the list of actions that were applied from the initial node to
        the goal node.
        """
        solution = []
        while self.parent is not None:
            solution.append(self.action)
            self = self.parent
        solution.reverse()
        return solution

    #TODO: not sure if im doing it right
    def __hash__(self):
        return self.hash_node
        
        
    def __eq__(self, other):
        return self.state == other.state and self.task_network == other.task_network

    def __str__(self):
        if type(self.state) == int:
            state_str = ''
        else:    
            state_str = '[\n\t\t' + '\n\t\t'.join(self.state) + ']'
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

class BlindNode(HTNNode):
    def __lt__(self, other):
        return self.seq_num < other.seq_num

class AstarNode(HTNNode):
    def __lt__(self, other):
        if self.heuristic + self.g_value ==  other.heuristic + other.g_value:
            if self.heuristic == other.heuristic:
                return self.seq_num < other.seq_num
            return self.heuristic < other.heuristic
        return self.heuristic + self.g_value <  other.heuristic + other.g_value
