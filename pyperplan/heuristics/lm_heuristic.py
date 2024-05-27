
from .heuristic import Heuristic
from ..model import Operator, AbstractTask
from ..utils import UNSOLVABLE
from .landmarks.and_or_graphs import AndOrGraph, NodeType, ContentType
from .landmarks.sccs import SCCDetection
from .landmarks.landmark import Landmarks, LM_Node
from collections import deque 
import time

'''
    Use a AndOr graph to perform a reachability analysis into a htn problem.
    Check if goal node is reachable (set of facts)
'''
class LandmarkHeuristic(Heuristic):
    def __init__(self, model, initial_node):
        super().__init__(model, initial_node)
        self.landmarks = None
        self.sccs = None # not working

        self.landmarks       = Landmarks(self.model)
        initial_node.lm_node = LM_Node(self.landmarks.len_landmarks)
        self.landmarks.bottom_up_lms()
        self.landmarks.top_down_lms()
        initial_node.lm_node.update_lms(self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network))
        
        for fact_pos in range(len(bin(initial_node.state))-2):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)
        
        initial_node.h_value = initial_node.lm_node.lm_value()
        initial_node.f_value = initial_node.h_value + initial_node.g_value
    
    def compute_heuristic(self, parent_node, node, debug=False):
        node.lm_node = LM_Node(self.landmarks.len_landmarks, parent=parent_node.lm_node)
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        
        # in case there is a change in the state:
        if type(node.task) is Operator:
            for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                if node.task.add_effects_bitwise & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
                
        node.h_value = node.lm_node.lm_value()
        node.f_value = node.h_value + node.g_value

    '''
    Useful for debug :
     printing achieved landmarks during heuristic search doesnt print the goal node
     just the node at the momento before picking goal node, which can diverge a lot in
     the number of reached lms;
    '''
    def check_final(self, astarnode):
        from ..search.htn_node import HTNNode
        print(f'\n\n\nPRINTING PATH')
        curr_node = astarnode
        print(f'curr_node.parent {curr_node} {curr_node.parent}')
        while curr_node.parent is not None:
            
            if type(curr_node.task) is Operator:
                print(f'\t({curr_node.task.global_id}) {curr_node.task.name}')
            else:
                print(f'\t({curr_node.task.global_id})=>({curr_node.decomposition.global_id}) {curr_node.task.name}: {curr_node.decomposition.name}')
            #print(sorted(list(curr_node.lm_node.lm_set - curr_node.lm_node.visited_set)))
            print(curr_node.lm_node)
            print()
            break
            curr_node = curr_node.parent