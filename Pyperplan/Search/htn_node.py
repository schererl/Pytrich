from Pyperplan.model import Operator
class HTNNode:
    def __init__(self, parent, task, decomposition, state, task_network, seq_num, g_value):
        # HTN info
        self.state  = state
        self.parent = parent
        self.task   = task
        self.decomposition = decomposition
        self.task_network  = task_network
        
        # Astar info
        self.seq_num = seq_num
        self.h_value = 0
        self.f_value = g_value
        self.g_value = g_value 

        # Heursitics info
        self.lm_node = None # for landmarks
        self.lp_vars = None # for TDGLm
        
        # NOTE: only use if we search considering visited nodes -high computational cost
        self.hash_node = hash((self.state, tuple(task_network)))
    
    def extract_solution(self):
        """
        Returns the list of actions that were applied from the initial node to
        the goal node.
        """
        plan_path = []
        goal_dist = []
        operators = []
        while self.parent is not None:
            goal_dist.append(self.task)
            plan_path.append(self.task)
            if isinstance(self.task, Operator):
                operators.append(self.task)
            else:
                plan_path.append(self.decomposition)

            self = self.parent
        plan_path.reverse()
        goal_dist.reverse()
        operators.reverse()
        return plan_path, operators, goal_dist

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
        # memory_info = (
        #     f"\n\tMemory Usage:"
        #     f"\n\t\tState: {sys.getsizeof(self.state)} bytes"
        #     f"\n\t\tParent: {sys.getsizeof(self.parent)} bytes"
        #     f"\n\t\tAction: {sys.getsizeof(self.action)} bytes"
        #     f"\n\t\tTask Network: {sys.getsizeof(self.task_network)} bytes"
        #)
        return (
            f"HTNNode: \n\tState: {{{state_str}}}"
            # f"\n\tAction: {self.action}"
            f"\n\tTaskNetwork: {self.task_network[0:min(5, len(self.task_network))]}"
            #f"\n{memory_info}"
        )


class AstarNode(HTNNode):
    def __lt__(self, other):
        if self.f_value ==  other.f_value:
            if self.h_value == other.h_value:
                return self.seq_num < other.seq_num
            return self.h_value < other.h_value
        return self.f_value < other.f_value
    