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
    def __init__(self, model):
        super().__init__(model)
        self.landmarks = None
        self.sccs = None # not working
        
    def compute_heuristic(self, parent_node, node, debug=False):
        # if debug:
        #     self.testing_landmark()
        if not parent_node:
            #self.andor_graph = AndOrGraph(model, top_down=False)
            self.landmarks   = Landmarks(self.model)
            node.lm_node     = LM_Node(self.landmarks.len_landmarks)
            self.landmarks.bottom_up_lms()
            self.landmarks.top_down_lms()
            node.lm_node.update_lms(self._bidirectional_lms(self.model, node.state, node.task_network))
        else:
            node.lm_node = LM_Node(self.landmarks.len_landmarks, parent=parent_node.lm_node)
            # mark last reached task (also add decomposition here)
            node.lm_node.mark_lm(node.task.global_id)
            
            # in case there is a change in the state:
            if type(node.task) is Operator:
                for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                    if node.state & (1 << fact_pos):
                        node.lm_node.mark_lm(fact_pos)
            else: #otherwise mark the decomposition
                node.lm_node.mark_lm(node.decomposition.global_id)
        
        # print(f'lms not fullyfilled:\n {node.lm_node}')
        # str_binlms = bin(node.lm_node.lms)[2:][::-1]
        # str_binreachlms = bin(node.lm_node.mark)[2:][::-1]
        # for lm_pos, lm_val in enumerate(str_binlms):
        #     if lm_val == '1':
        #         print(f"lm: {lm_val} {str_binreachlms[lm_pos] if len(str_binreachlms) > lm_pos else '0'} {self.andor_graph.nodes[lm_pos]}")
        
        return node.lm_node.lm_value()
    
    def _bidirectional_lms(self, model, state, task_network):
        """
        Combination of bottom-up landmarks w/ top-down landmarks:
            - refine operators found by bottom-up landmarks using top-down landmarks
            - refine methods found by top-down landmarks using bottom-up landamrks
            - repeat until exausting every possible refinment 
        Args:
            model (Model): The planning model.
            state (int): Bitwise representation of the current state.
            task_network (list): List of tasks in the task network.

        Returns:
            set: Set of computed landmarks.
        """
        bid_landmarks = set()
        visited   = set()
        queue     = deque()
        # Precompute landmarks based on the initial state and goal conditions
        for fact_pos in range(len(bin(model.goals))-2):
            if model.goals & (1 << fact_pos) and ~state & (1 << fact_pos):
                for lm in self.landmarks.bu_landmarks[fact_pos]:
                    bid_landmarks.add(lm)
            if state & (1 << fact_pos):
                bid_landmarks.add(fact_pos)
        
        # Add landmarks related to each task in the task network
        for t in task_network:
            for lm in self.landmarks.bu_landmarks[t.global_id]:
                bid_landmarks.add(lm)
        
        for lm in bid_landmarks:
            node = self.landmarks.bu_AND_OR.nodes[lm]
            if node.content_type == ContentType.OPERATOR:
                queue.append(node.ID)
            else:
                visited.add(node.ID)
        
        # print(f'\n\nbottom-up landmarks {len(bid_landmarks)}')
        # for lm in bid_landmarks:
        #     print(self.landmarks.bu_AND_OR.nodes[lm])
        
        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue
            
            visited.add(node_id)
            bid_landmarks.add(node_id)
            node = self.landmarks.bu_AND_OR.nodes[node_id]
            if node.content_type == ContentType.OPERATOR:
                for lm_id in self.landmarks.td_landmarks[node.ID]:
                    if not lm_id in visited:
                        queue.append(lm_id)
            elif node.content_type == ContentType.METHOD:
                for lm_id in self.landmarks.bu_landmarks[node.ID]:
                    if not lm_id in visited:
                        queue.append(lm_id)

        # print(f'\n\nbidirectional landmarks {len(bid_landmarks)}')
        # for lm in bid_landmarks:
        #     print(self.landmarks.bu_AND_OR.nodes[lm])
        
        return bid_landmarks
    