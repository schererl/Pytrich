from pyperplan.heuristics.heuristic import Heuristic
from pyperplan.model import Operator
from pyperplan.heuristics.landmarks.landmark import Landmarks, LM_Node

class LandmarkHeuristic(Heuristic):
    """
    Use a AndOr graph to perform a reachability analysis into a htn problem.
    Check if goal node is reachable (set of facts)
    """
    def __init__(self, model, initial_node):
        super().__init__(model, initial_node)
        self.landmarks = None
        self.sccs = None # not working

        self.landmarks       = Landmarks(self.model)
        initial_node.lm_node = LM_Node()
        self.landmarks.bottom_up_lms()
        self.landmarks.top_down_lms()
        #test = self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network)
        #print([self.landmarks.bu_AND_OR.nodes[id] for id in test])
        #print([self.landmarks.bu_AND_OR.nodes[id] for id in self.landmarks.bu_landmarks[88]])
        #print([self.landmarks.td_AND_OR.nodes[id] for id in self.landmarks.td_landmarks[88]])
        #print([self.landmarks.td_AND_OR.nodes[id] for id in self.landmarks.td_AND_OR.nodes[88].successors])
        #print(self.landmarks.td_AND_OR.nodes[88].predecessors)
        #print(self.landmarks.td_AND_OR.nodes[88].successors)
        initial_node.lm_node.update_lms(self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network))
        
        for fact_pos in range(len(bin(initial_node.state))-2):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)
        
        initial_node.h_value = initial_node.lm_node.lm_value()
        initial_node.f_value = initial_node.h_value + initial_node.g_value
    
    def compute_heuristic(self, parent_node, node, debug=False):
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        
        # in case there is a change in the state:
        if isinstance(node.task, Operator):
            for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                if node.task.add_effects_bitwise & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
                
        node.h_value = node.lm_node.lm_value()
        node.f_value = node.h_value + node.g_value