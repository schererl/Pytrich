import time
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Operator, Model
from Pytrich.Heuristics.Landmarks.landmark import Landmarks, LM_Node
from Pytrich.Heuristics.Landmarks.falm import FALM
import Pytrich.FLAGS as FLAGS

class LandmarkHeuristic(Heuristic):
    """
    Compute landmarks and perform a sort of hamming distance with it (not admissible yet)
    """
    def __init__(self, model:Model, initial_node:HTNNode, on_reaching=False, use_disj=False, use_falm=False, use_bid=True, name="lmcount"):
        super().__init__(model, initial_node, name=name)
        # set parameters
        self.use_disj = use_disj
        self.use_falm = use_falm
        self.use_bid = use_bid
        self._define_param_str()

        # Initialize timing variables
        self.initt_andor_all = 0
        self.endt_andor_all = 0
        self.initt_mcdisj = 0
        self.endt_mcdisj = 0
        self.elapsed_andor_time = 0
        self.elapsed_mcdisj_time = 0

        self.landmarks = None
        self.sccs = None  # NOTE: not working

        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(self.model)

        if FLAGS.MONITOR_LM_TIME:
            self.initt_andor_all = time.perf_counter()

        self.landmarks.bottom_up_lms()

        if use_bid:
            if FLAGS.MONITOR_LM_TIME:
                self.initt_andor_td = time.perf_counter()

            self.landmarks.top_down_lms()
            initial_node.lm_node.update_lms(self.landmarks.bidirectional_lms(initial_node.state, initial_node.task_network))

            if FLAGS.MONITOR_LM_TIME:
                self.endt_andor_all = time.perf_counter()
                self.elapsed_andor_time = self.endt_andor_all - self.initt_andor_all

        else:
            initial_node.lm_node.update_lms(self.landmarks.classical_lms(initial_node.state, initial_node.task_network))

            if FLAGS.MONITOR_LM_TIME:
                self.endt_andor_all = time.perf_counter()
                self.elapsed_andor_time = self.endt_andor_all - self.initt_andor_all

        self.task_andor_lms = len(self.landmarks.task_lms)
        self.methods_andor_lms = len(self.landmarks.method_lms)
        self.fact_andor_lms = len(self.landmarks.fact_lms)
        self.total_andor_lms = self.task_andor_lms + self.methods_andor_lms + self.fact_andor_lms
        self.mc_disj_lms = 0

        if use_falm:
            f = FALM(self.model, self.landmarks)
            f._calculate_reachable()
            f._calculate_predecessors()
            f._check_all_hierachy_achievers()
            f.extract_landmarks()
            initial_node.lm_node.update_lms(f.landmark_set)
            exit()  # NOTE: unavailable work in progress

        if use_disj:
            if FLAGS.MONITOR_LM_TIME:
                self.initt_mcdisj = time.perf_counter()

            self.landmarks._compute_minimal_disjunctions()
            self.mc_disj_lms = len(self.landmarks.valid_disjunctions)
            initial_node.lm_node.update_disjunctions(self.landmarks.valid_disjunctions)

            if FLAGS.MONITOR_LM_TIME:
                self.endt_mcdisj = time.perf_counter()
                self.elapsed_mcdisj_time = self.endt_mcdisj - self.initt_mcdisj

        # clear lm structures and and-or-graph
        self.landmarks.clear_structures()
        for fact_pos in range(len(bin(initial_node.state)) - 2):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)
        if use_disj:
            initial_node.lm_node.mark_disjunction(initial_node.state)

        self.on_reaching = on_reaching
        if self.on_reaching:
            for task in self.model.initial_tn:
                initial_node.lm_node.mark_lm(task.global_id)

        super().set_h_f_values(initial_node, initial_node.lm_node.lm_value())
        self.initial_h = initial_node.h_value
    
    def __call__(self, parent_node:HTNNode, node:HTNNode):
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        
        # in case there is a change in the state:
        if isinstance(node.task, Operator):
            for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                if node.task.add_effects_bitwise & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
                
                if self.use_disj:
                    node.lm_node.mark_disjunction(node.state)        

        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
            if self.on_reaching:
                for t in node.decomposition.task_network:
                    node.lm_node.mark_lm(t.global_id)
                
        super().set_h_f_values(node,  node.lm_node.lm_value())

    def _define_param_str(self):
        self.param_str = '_'
        if self.use_bid:
            self.param_str+='B'
        else:
            self.param_str+='C'
        self.param_str+='_'
        if self.use_falm:
            self.param_str+='F'
            self.param_str+='_'
        if self.use_disj:
            self.param_str+='D'
            self.param_str+='_'
            
    def __output__(self):
        # Get the singleton instance of Descriptions
        desc = Descriptions()

        out_str = f'Heuristic Info:\n'
        out_str += f'\t{desc("heuristic_name", self.name)}\n'
        out_str += f'\t{desc("total_landmarks", self.total_andor_lms)}\n'
        out_str += f'\t{desc("task_landmarks", self.task_andor_lms)}\n'
        out_str += f'\t{desc("method_landmarks", self.methods_andor_lms)}\n'
        out_str += f'\t{desc("fact_landmarks", self.fact_andor_lms)}\n'
        out_str += f'\t{desc("mincov_disj_landmarks", self.mc_disj_lms)}\n'

        if FLAGS.MONITOR_LM_TIME:
            out_str += f'\t{desc("heuristic_elapsed_time", f"{self.elapsed_andor_time:.4f}")}\n'
            out_str += f'\t{desc("mincov_disj_elapsed_time", f"{self.elapsed_mcdisj_time:.4f}")}\n'

        return out_str