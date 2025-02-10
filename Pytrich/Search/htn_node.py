from typing import List, Optional, Union
from Pytrich.model import AbstractTask, Decomposition, Operator

class HTNNode:
    G: Optional[int] = 1
    H: Optional[int] = 1

    def __init__(self, parent: Optional['HTNNode'],
                 task: Union[Operator, AbstractTask],
                 decomposition: Optional[Decomposition],
                 state: Union[int, set],
                 task_network: List[Union[Operator, AbstractTask]],
                 seq_num: int,
                 H: Optional[float] = None,
                 G: Optional[float] = None):
        # HTN info
        self.state = state
        self.parent = parent
        self.task = task
        self.decomposition = decomposition
        self.task_network: List[Union[Operator, AbstractTask]] = task_network
        
        # Node value info
        self.seq_num  = seq_num
        self.h_value = 0
        self.g_value = 0
        if G is not None:
            HTNNode.G = G
        if H is not None:
            HTNNode.H = H
        # Heursitics info
        self.lm_node = None # for landmarks
        # NOTE: only use if we search considering visited nodes -high computational cost
        self.hash_node = hash((self.state, tuple(task_network)))

        
    def update_g_h(self, g_value, h_value):
        self.h_value = h_value
        self.g_value = g_value
    
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
        return f"function F = {self.G}*G + {self.H}*H"

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

class GreedyNode(HTNNode):
    def __lt__(self, other):
        return (self.h_value, self.g_value) < (other.h_value, other.g_value)


class AstarNode(HTNNode):
    def __lt__(self, other):
        #print(self.h_values)
        return (self.g_value*HTNNode.G + self.h_value*HTNNode.H, \
                self.h_value, \
                self.seq_num) \
                < \
                (other.g_value*HTNNode.G + other.h_value*HTNNode.H, \
                other.h_value, \
                other.seq_num)


class TiebreakingNode(HTNNode):
    def __lt__(self, other):
        #print(self.h_values)
        return (self.g_value*HTNNode.G + self.h_value[0]*HTNNode.H, \
                self.h_value, \
                self.seq_num) \
                < \
                (other.g_value*HTNNode.G + other.h_value[0]*HTNNode.H, \
                other.h_value, \
                other.seq_num)


    