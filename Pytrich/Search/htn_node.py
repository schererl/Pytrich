from typing import List, Optional, Union
from Pytrich.model import AbstractTask, Decomposition, Operator

class HTNNode:
    h_multiplier: Optional[int] = 1
    g_multiplier: Optional[int] = 1

    def __init__(self, parent: Optional['HTNNode'], task: Union[Operator, AbstractTask],
                 decomposition: Optional[Decomposition], state: Union[int, set],
                 task_network: List[Union[Operator, AbstractTask]], seq_num: int, g_value: int, 
                 H: Optional[float] = None, G: Optional[float] = None):
        # HTN info
        self.state = state
        self.parent = parent
        self.task = task
        self.decomposition = decomposition
        self.task_network: List[Union[Operator, AbstractTask]] = task_network
        
        # Astar info
        self.seq_num = seq_num
        self.h_value = 0
        self.g_value = g_value
        self.f_value = 0
        # Heursitics info
        self.lm_node = None # for landmarks
        self.lp_vars = None # for TDGLm
        
        # NOTE: only use if we search considering visited nodes -high computational cost
        self.hash_node = hash((self.state, tuple(task_network)))
    
        if G is not None and H is not None:
            HTNNode.h_multiplier = H
            HTNNode.g_multiplier = G
        

    def compute_f(self):
        self.f_value = HTNNode.h_multiplier * self.h_value + HTNNode.g_multiplier * self.g_value

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
            if isinstance(self.task, Operator) and self.task.cost!=0:
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
        
    def __output__(self):
        return f"function F = {self.g_multiplier}*G + {self.h_multiplier}*H"

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
    