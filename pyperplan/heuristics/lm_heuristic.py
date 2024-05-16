from .heuristic import Heuristic
from ..model import Operator, AbstractTask
from ..utils import UNSOLVABLE
from .landmarks.and_or_graphs import AndOrGraph, NodeType, ContentType
from .landmarks.sccs import SCCDetection
from .landmarks.landmark import Landmarks, LM_Node
from ..search.htn_node import AstarLMNode
from collections import deque 
import time
'''
    Use a AndOr graph to perform a reachability analysis into a htn problem.
    Check if goal node is reachable (set of facts)
'''
class LandmarkHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
        self.andor_graph = None
        self.sccs = None # not working
        self.landmarks = None
        self.exit_count = 0
        self.exit_limit = 1
        
    def compute_heuristic(self, model, parent_node, node, debug=False):
        assert type(node) == AstarLMNode
        # if debug:
        #     self.testing_landmark()
        if not parent_node:
            self.andor_graph = AndOrGraph(model, top_down=False)
            node.lm_node     = LM_Node(len(self.andor_graph.nodes))
            self.landmarks   = Landmarks(self.andor_graph)
            self.landmarks.generate_lms()
            
            self.landmarks2   = Landmarks(AndOrGraph(model, top_down=True))
            self.landmarks2.top_down_lms()
            node.lm_node.update_lms(self.bidirectional_lms(model, node.state, node.task_network))
        else:
            node.lm_node = LM_Node(len(self.andor_graph.nodes), parent=parent_node.lm_node)
            # mark last reached task (also add decomposition here)
            node.lm_node.mark_lm(node.task.global_id)
            
            # in case there is a change in the state:
            if type(node.task) is Operator:
                for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                    if node.state & (1 << fact_pos):
                        node.lm_node.mark_lm(fact_pos)
            else: #otherwise mark the decomposition
                node.lm_node.mark_lm(node.decomposition.global_id)
        return node.lm_node.lm_value()
    
    def bidirectional_lms(self, model, state, task_network):
        """
        Precompute bidirectional landmarks for initial task network considering both top-down and bottom-up approaches.

        Args:
            model (Model): The planning model.
            state (int): Bitwise representation of the current state.
            task_network (list): List of tasks in the task network.

        Returns:
            set: Set of computed landmarks.
        """
        landmarks = set()
        visited   = set()
        queue     = deque()
        # Precompute landmarks based on the initial state and goal conditions
        for fact_pos in range(len(bin(model.goals))-2):
            if model.goals & (1 << fact_pos) and ~state & (1 << fact_pos):
                for lm in self.landmarks.landmarks[fact_pos]:
                    landmarks.add(lm)
            if state & (1 << fact_pos):
                landmarks.add(fact_pos)
        # Add landmarks related to each task in the task network
        for t in task_network:
            self.landmarks.print_landmarks(t.global_id)
            for lm in self.landmarks.landmarks[t.global_id]:
                landmarks.add(lm)
        
        for lm in landmarks:
            node = self.andor_graph.nodes[lm]
            if node.content_type == ContentType.OPERATOR:
                queue.append(node.ID)
            else:
                visited.add(node.ID)
        
        # print(f'\n\nbottom-up landmarks')
        # for lm in landmarks:
        #     print(self.andor_graph.nodes[lm])
        
        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue
            
            visited.add(node_id)
            landmarks.add(node_id)
            node = self.andor_graph.nodes[node_id]
            if node.content_type == ContentType.OPERATOR:
                for lm_id in self.landmarks2.landmarks[node.ID]:
                    if not lm_id in visited:
                        queue.append(lm_id)
            elif node.content_type == ContentType.METHOD:
                for lm_id in self.landmarks.landmarks[node.ID]:
                    if not lm_id in visited:
                        queue.append(lm_id)

        # print(f'\n\nbidirectional landmarks:')
        # for lm in landmarks:
        #     print(self.andor_graph.nodes[lm])
        return landmarks
    