import time
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Operator, Model
from Pytrich.Heuristics.Landmarks.landmark import Landmarks, LM_Node
import Pytrich.FLAGS as FLAGS

class LandmarkHeuristic(Heuristic):
    """
    Compute landmarks and perform a sort of hamming distance with it (not admissible yet)
    """
    #TODO: implement LAZY and EAGER task landmark detection
    def __init__(self, model:Model, initial_node:HTNNode, use_ord=False, use_disj=False, use_bid=False, name="lmcount"):
        super().__init__(model, initial_node, name=name)
        # set parameters
        self.use_disj = use_disj
        self.use_bid = use_bid
        self.use_ord = use_ord
        self._define_param_str()

        # Initialize timing variables
        self.initt_andor_all = 0
        self.endt_andor_all  = 0
        self.initt_mcdisj    = 0
        self.endt_mcdisj     = 0
        self.elapsed_andor_time  = 0
        self.elapsed_mcdisj_time = 0

        self.landmarks = None
        self.sccs = None  # NOTE: not working

        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(self.model, use_bid)

        if FLAGS.MONITOR_LM_TIME:
            self.initt_andor_all = time.perf_counter()

        self.landmarks.generate_bottom_up()
        self.landmarks.bottom_up_lms()
        if self.use_ord:
            self.landmarks.compute_gn_orderings(self.landmarks.bu_lookup, self.landmarks.bu_graph)
        if use_bid: # TODO: top-down and bid not working
            if FLAGS.MONITOR_LM_TIME:
                self.initt_andor_td = time.perf_counter()
            self.landmarks.generate_top_down()
            self.landmarks.top_down_lms()
            self.landmarks.bidirectional_lms()
            self.landmarks.identify_lms(self.landmarks.bid_lms)
            initial_node.lm_node.initialize_lms(self.landmarks.bid_lms)
            if FLAGS.MONITOR_LM_TIME:
                self.endt_andor_all = time.perf_counter()
                self.elapsed_andor_time = self.endt_andor_all - self.initt_andor_all

        else:
            initial_node.lm_node.initialize_lms(self.landmarks.bu_lms)
            self.landmarks.identify_lms(self.landmarks.bu_lms)
            if FLAGS.MONITOR_LM_TIME:
                self.endt_andor_all = time.perf_counter()
                self.elapsed_andor_time = self.endt_andor_all - self.initt_andor_all

        self.task_andor_lms    = self.landmarks.count_task_lms
        self.methods_andor_lms = self.landmarks.count_method_lms
        self.fact_andor_lms    = self.landmarks.count_fact_lms
        self.total_andor_lms   = self.task_andor_lms + self.methods_andor_lms + self.fact_andor_lms
        self.mc_disj_lms = 0

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

        super().set_h_f_values(initial_node, initial_node.lm_node.lm_value())
        self.initial_h = initial_node.h_value
    
    def __call__(self, parent_node:HTNNode, node:HTNNode):
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        
        # in case there is a change in the state:
        if isinstance(node.task, Operator):
            for fact_pos in range(node.task.add_effects.bit_length()):
                if node.task.add_effects & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
                if self.use_disj:
                    node.lm_node.mark_disjunction(node.state)
            # orderings: deleted facts can reactivate fact landmarks
            if self.use_ord and (node.task.del_effects & node.lm_node.mark):  # if a fact landmark is deleted
                self._deal_with_ordering(node, parent_node)        
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
            
                
        super().set_h_f_values(node,  node.lm_node.lm_value())

    def _deal_with_ordering(self, node, parent_node):
        # get the set of accepted landmarks that are deleted by this operator
        deleted_lm_facts = node.lm_node.mark & node.task.del_effects
        for bit_pos in range(deleted_lm_facts.bit_length()):
            # if fact was true and deleted:
            if deleted_lm_facts & (1 << bit_pos) and parent_node.state & (1 << bit_pos):
                is_goal_fact = self.model.goals & (1 << bit_pos)
                # if ϕ is part of the goal or required before another landmark
                required_again = False
                if is_goal_fact:
                    required_again = True
                else:
                    # if there exists ψ such that ϕ →gn ψ and ψ is not accepted in s
                    for psi in self.landmarks.lm_gn_orderings[bit_pos]:
                        psi_accepted = node.lm_node.mark & (1 << psi)
                        if not psi_accepted:
                            required_again = True
                            break
                    
                if required_again:
                    # landmark ϕ needs to be required again
                    node.lm_node.mark &= ~(1 << bit_pos)  # unmark the landmark as accepted
                    node.lm_node.achieved_lms -= 1        # decrease the count of achieved landmarks

    def _define_param_str(self):
        self.param_str = '_'
        if self.use_bid:
            self.param_str+='B'
        else:
            self.param_str+='C'
        self.param_str+='_'
        if self.use_disj:
            self.param_str+='D'
            self.param_str+='_'
        if self.use_ord:
            self.param_str+='GN'
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