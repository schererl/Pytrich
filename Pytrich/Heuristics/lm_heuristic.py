import time
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import AbstractTask, Operator, Model
from Pytrich.Heuristics.Landmarks.landmark import Landmarks, LM_Node
import Pytrich.FLAGS as FLAGS

class LandmarkHeuristic(Heuristic):
    """
    Compute landmarks and perform a sort of hamming distance with it (not admissible yet)
    Options:
        use_task_ord: <NOT WORKING YET> generate task orderings using greedy necessary orderings to reactivate task landmarks in lmcount (requires top-down graph)
        use_fact_ord: <NOT WORKING YET> generate fact orderings using greedy necessary orderings to reactivate fact landmarks in lmcount
        use_bid: generate bidirectional landmarks (ICAPS25 submission)
        use_disj: <UNAVAILABLE> compute disjunctive landmarks over facts with minimal hitting set over fatcs (work in progress)
        use_bu_update: updates landmarks based on node's task network
    """
    
    def __init__(   self, model:Model,
                    initial_node:HTNNode,
                    use_task_ord=False,
                    use_fact_ord=False,
                    use_disj=False,
                    use_bid=False,
                    use_bu_update=False,
                    name="lmcount"
                ):
        super().__init__(model, initial_node, name=name)
        # set parameters
        self.use_disj = use_disj
        self.use_bid  = use_bid
        self.use_task_ord  = use_task_ord
        self.use_fact_ord  = use_fact_ord
        self.use_bu_update = use_bu_update
        
        self._define_param_str()

        # Initialize timing variables
        self.initt_andor_all = 0
        self.endt_andor_all  = 0
        self.initt_mcdisj    = 0
        self.endt_mcdisj     = 0
        self.elapsed_andor_time  = 0
        self.elapsed_mcdisj_time = 0
        self.task_lm_reactivations = 0
        self.fact_lm_reactivations = 0

        self.landmarks = None
        self.sccs = None  # NOTE: not working

        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(self.model, use_bid)

        if FLAGS.MONITOR_LM_TIME:
            self.initt_andor_all = time.perf_counter()

        self.landmarks.generate_bu_table()
        self.landmarks.bottom_up_lms(self.model.initial_state, self.model.initial_tn)
        if use_bid: # TODO: top-down and bid not working
            if FLAGS.MONITOR_LM_TIME:
                self.initt_andor_td = time.perf_counter()
            self.landmarks.generate_td_table()
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

        if self.use_task_ord:
            assert use_bid is True
            self.landmarks.compute_gn_task_orderings(self.landmarks.td_lookup, self.landmarks.td_graph, self.landmarks.td_lms)
        if self.use_fact_ord:
            self.landmarks.compute_gn_fact_orderings(self.landmarks.td_lookup, self.landmarks.td_graph, self.landmarks.td_lms)
            

        self.task_andor_lms    = self.landmarks.count_task_lms
        self.methods_andor_lms = self.landmarks.count_method_lms
        self.fact_andor_lms    = self.landmarks.count_fact_lms
        self.total_andor_lms   = self.task_andor_lms + self.methods_andor_lms + self.fact_andor_lms
        self.mc_disj_lms = 0
        # NOTE: minimal disjunctions not working
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
        #self.landmarks.clear_structures()
        for fact_pos in range(len(bin(initial_node.state)) - 2):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)
        if use_disj:
            initial_node.lm_node.mark_disjunction(initial_node.state)

        super().set_h_f_values(initial_node, initial_node.lm_node.lm_value())
        self.initial_h = initial_node.h_values[0]
    
    def __call__(self, parent_node:HTNNode, node:HTNNode):
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        if self.use_bu_update:
            #self.landmarks.generate_bu_table(node.state, reinitialize=False)
            self.landmarks.bottom_up_lms(node.state, node.task_network, reinitialize=False)
            node.lm_node.update_lms(self.landmarks.bu_lms)
            

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
            if self.use_task_ord and (node.task.del_effects & node.lm_node.mark):  # fact landmark is deleted
                self._deal_with_fact_ordering(node, parent_node)
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
            if self.use_fact_ord and (node.task.global_id & node.lm_node.lms): # task landmark applied ('delete' task from task network)
                self._deal_with_task_ordering(node, parent_node)
        
            
                
        super().set_h_f_values(node,  node.lm_node.lm_value())

    def _deal_with_fact_ordering(self, node: HTNNode, parent_node: HTNNode):
        """
        Handles the scenario where a landmark fact that was previously satisfied 
        might need to be re-established due to the current action's delete effects.

        Specifically:
        Fact Landmarks:
        - If a landmark fact is deleted by the current operator, determine if it will be 
            required again later (e.g., it is part of the goal, or there exist other landmarks 
            that depend on it). If so, unmark it as 'achieved' so that the planner continues 
            to treat it as a necessary condition.
        """

        # -- Handle Fact Orderings/Dependencies --
        if self.landmarks.gn_fact_orderings:
            # Retrieve any fact landmarks deleted by the current operator.
            deleted_lm_facts = node.lm_node.mark & node.task.del_effects
            for bit_pos in range(deleted_lm_facts.bit_length()):
                if deleted_lm_facts & (1 << bit_pos):  # If a landmark fact was deleted
                    # Check if it was actually satisfied in the parent's state
                    if parent_node.state & (1 << bit_pos):
                        is_goal_fact = (self.model.goals & (1 << bit_pos)) != 0
                        required_again = False

                        # If it's a goal fact, it is automatically needed again
                        if is_goal_fact:
                            required_again = True
                        else:
                            # Check other landmark facts that depend on this fact
                            for psi in self.landmarks.gn_fact_orderings[bit_pos]:
                                # If psi is not yet accepted, fact is needed again
                                if not (node.lm_node.mark & (1 << psi)):
                                    required_again = True
                                    break

                        if required_again:
                            # Unmark the fact landmark so it can be re-established
                            node.lm_node.mark &= ~(1 << bit_pos)
                            node.lm_node.achieved_lms -= 1
                            self.fact_lm_reactivations+=1

    def _deal_with_task_ordering(self, node: HTNNode, parent_node: HTNNode):
        """
        Handles the scenario where a landmark task that was previously satisfied 
        might need to be re-established due to the current action's task's decomposition
        
        Task Orderings (under GN ordering constraints): *new stuff
        - If the current node's task is itself a landmark task, check whether there exist 
            other landmark tasks that depend on its completion. If those dependent tasks are 
            not yet achieved and are not reachable from the current node's decomposition, 
            re-flag the current task as "required" again.

        """
        # -- Handle Task Orderings/Dependencies --
        if len(self.landmarks.gn_task_orderings[node.task.global_id-len(self.model.facts)]) == 0:
            return
    
        # The current node's task is a recognized landmark task. Check if this task
        # needs to remain "active" because other tasks in the decomposition rely on it.
        required_again = False
        # Determine which tasks are reachable from the current decomposition
        reachable_tasks = 0
        for t in node.decomposition.task_network:
            reachable_tasks |= (1 << t.global_id)
        # Check tasks that require the current one to be completed (GN ordering)
        for psi in self.landmarks.gn_task_orderings[node.task.global_id-len(self.model.facts)]:
            # If psi is a landmark task not yet achieved and not reachable from here,
            # the current task may need to stay "unresolved" to enforce ordering.
            psi_accepted = (node.lm_node.mark & (1 << psi)) != 0
            psi_reachable = (reachable_tasks & (1 << psi)) != 0
            if (node.lm_node.lms & (1 << psi)) and (not psi_accepted) and (not psi_reachable):
                # print(f'\norderings of {node.task.name}')
                # print(f'\t-> {self.model.get_component(psi).name}')
                # print(f'\trequired again, pikced {node.decomposition.name}' )
                required_again = True
                break

        if required_again:
            # print(f'task requires again {node.task.name}')
            # Unmark the current landmark task to indicate it must remain "open"
            node.lm_node.mark &= ~(1 << node.task.global_id)
            #print(node.lm_node.lm_value())
            node.lm_node.achieved_lms -= 1
            #print(node.lm_node.lm_value())
            self.task_lm_reactivations+=1


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
        if self.use_task_ord:
            self.param_str+='Tord'
            self.param_str+='_'
        if self.use_fact_ord:
            self.param_str+='Ford'
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
        out_str += f'\t{desc("fact_reactivations", self.fact_lm_reactivations)}\n'
        out_str += f'\t{desc("task_reactivations", self.fact_lm_reactivations)}\n'

        if FLAGS.MONITOR_LM_TIME:
            out_str += f'\t{desc("heuristic_elapsed_time", f"{self.elapsed_andor_time:.4f}")}\n'
            out_str += f'\t{desc("mincov_disj_elapsed_time", f"{self.elapsed_mcdisj_time:.4f}")}\n'

        return out_str