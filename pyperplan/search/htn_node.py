import sys
USE_ASTAR = False
class HTNNode:
    
    def __init__(self, state, parent, action, task_network, seq_num, g_value, heuristic):
        self.state = state
        self.parent = parent
        self.action = action
        self.task_network = task_network
        self.seq_num = seq_num
        self.heuristic = heuristic
        self.g_value = g_value
    
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

    def __lt__(self, other):
        if USE_ASTAR:
            if self.heuristic + self.g_value ==  other.heuristic + other.g_value:
                if self.heuristic == other.heuristic:
                    return self.seq_num < other.seq_num
                return self.heuristic < other.heuristic
            return self.heuristic + self.g_value <  other.heuristic + other.g_value
        
        return self.seq_num < other.seq_num
    
    #NOTE: verify if this is fully functional
    def __hash__(self):
        return hash((self.state, tuple(self.task_network)))
        
    def __eq__(self, other):
        return self.state == other.state and self.task_network == other.task_network

    def __str__(self):
        state_str = '[\n\t\t' + '\n\t\t'.join(self.state) + ']'
        memory_info = (
            f"\n\tMemory Usage:"
            f"\n\t\tState: {sys.getsizeof(self.state)} bytes"
            f"\n\t\tParent: {sys.getsizeof(self.parent)} bytes"
            f"\n\t\tAction: {sys.getsizeof(self.action)} bytes"
            f"\n\t\tTask Network: {sys.getsizeof(self.task_network)} bytes"
        )
        return (
            # f"HTNNode: \n\tState: {{{state_str}}}"
            # f"\n\tAction: {self.action}"
            # f"\n\tTaskNetwork: {self.task_network[0:min(5, len(self.task_network))]}"
            f"HTNNode: \n{memory_info}"
        )

def make_node(parent_node, action, state, task_network, seq_num=0, g_value=0, heuristic=0):
    return HTNNode(state, parent_node, action, task_network, seq_num, g_value, heuristic)


