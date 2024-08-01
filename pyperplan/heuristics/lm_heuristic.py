from pyperplan.heuristics.heuristic import Heuristic
from pyperplan.model import Operator
from pyperplan.heuristics.landmarks.landmark import Landmarks, LM_Node
from pyperplan.heuristics.landmarks.falm import FALM
class LandmarkHeuristic(Heuristic):
    """
        Compute landmarks and perform a sort of hamming distance with it (not admissible yet)
    """
    def __init__(self, model, initial_node, on_reaching=False, use_falm=False, use_bid=True, name="lmcount"):
        super().__init__(model, initial_node, name=name)
        
        self.landmarks = None
        self.sccs = None # not working
        initial_node.lm_node = LM_Node()
        if use_falm:
            f = FALM(self.model)
            f.extract_landmarks()
            initial_node.lm_node.update_lms(f.landmark_set)
            initial_node.lm_node.update_disjunctions(f.valid_disjunctions)
        else:
            self.landmarks       = Landmarks(self.model)
            self.landmarks.bottom_up_lms()
            if use_bid:
                self.landmarks.top_down_lms()
                initial_node.lm_node.update_lms(self.landmarks.bidirectional_lms(self.model, initial_node.state, initial_node.task_network))
            else:
                initial_node.lm_node.update_lms(self.landmarks.classical_lms(self.model, initial_node.state, initial_node.task_network))

        
        for fact_pos in range(len(bin(initial_node.state))-2):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)
        initial_node.lm_node.mark_disjunction(initial_node.state)        


        self.on_reaching=on_reaching
        if self.on_reaching:
            for task in self.model.initial_tn:
                initial_node.lm_node.mark_lm(task.global_id)

        super().set_hvalue(initial_node, initial_node.lm_node.lm_value())
        self.initial_h = initial_node.h_value
        
    
    def compute_heuristic(self, parent_node, node, debug=False):
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        
        # in case there is a change in the state:
        if isinstance(node.task, Operator):
            for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                if node.task.add_effects_bitwise & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
                node.lm_node.mark_disjunction(node.state)        
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
            if self.on_reaching:
                for t in node.decomposition.task_network:
                    node.lm_node.mark_lm(t.global_id)
                
        super().set_hvalue(node,  node.lm_node.lm_value())