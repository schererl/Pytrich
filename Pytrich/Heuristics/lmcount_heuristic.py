import time
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.Landmarks.bit_lm_node import BitLm_Node
from Pytrich.Heuristics.Landmarks.landmark import Landmarks
from Pytrich.Heuristics.Landmarks.landmark_cut import LMCutRC
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import AbstractTask, Operator, Model
import Pytrich.FLAGS as FLAGS
#TODO: need code refactor
# landmark should have a lm_index that is different from global_id (at least not necessarily equal)
# this is implemented in UCP and lm-cut lms
class LandmarkCountHeuristic(Heuristic):
    """
    Compute landmarks and perform a sort of hamming distance with it (not admissible yet)
    Options:
        use_task_ord: <NOT WORKING YET> generate task orderings using greedy necessary orderings to reactivate task landmarks in lmcount (requires top-down graph)
        use_fact_ord: <NOT WORKING YET> generate fact orderings using greedy necessary orderings to reactivate fact landmarks in lmcount
        use_bid: generate bidirectional landmarks (ICAPS25 submission)
        use_disj: <UNAVAILABLE> compute disjunctive landmarks over facts with minimal hitting set over fatcs (work in progress)
        use_bu_update: updates landmarks based on node's task network
        use_bu_strict: bottom-up landmarks without mandatory tasks
    """
    
    def __init__(self,
                 use_task_ord=False,
                 use_fact_ord=False,
                 use_disj=False,
                 use_bid=False,
                 use_mt=False,
                 use_bu_update=False,
                 use_bu_strict=False,
                 use_lmc=False,
                 use_ucp=False,
                 name="lmcount"):
        super().__init__(name=name)
        self.use_bid = use_bid
        self.use_mt = use_mt
        self.use_bu_strict = use_bu_strict
        self.use_bu_update = use_bu_update
        self.use_lmc = use_lmc
        self.use_disj = use_disj
        self.use_task_ord = use_task_ord
        self.use_fact_ord = use_fact_ord
        self.use_ucp = use_ucp

        
        self._define_param_str()

        self.landmarks = None
        
        # Timing and statistics
        self.start_time = 0
        self.elapsed_andor_time=0
        self.elapsed_andor_time = 0
        self.elapsed_mcdisj_time = 0
        self.task_lm_reactivations = 0
        self.fact_lm_reactivations = 0

        self.total_lms    = 0
        self.abtask_lms   = 0
        self.operator_lms = 0
        self.methods_lms  = 0
        self.fact_lms     = 0
        self.disjunction_lms = 0

    def initialize(self, model, initial_node):
        """Generate and initialize landmarks."""
        self.start_time = time.perf_counter()
        
        if self.use_bid:
            self.landmarks = Landmarks(model, True, True, False)
            self.landmarks.generate_bu_table()
            self.landmarks.bottom_up_lms(model.initial_state, model.initial_tn)
            self.landmarks.generate_td_table()
            self.landmarks.top_down_lms()
            self.landmarks.bidirectional_lms()
            self.landmarks.identify_lms(self.landmarks.bid_lms, self.landmarks.bu_graph)
            initial_node.lm_node = BitLm_Node()
            initial_node.lm_node.initialize_lms(self.landmarks.bid_lms)
        elif self.use_mt:
            self.landmarks =Landmarks(model, False, False, True)
            self.landmarks.generate_mt_table()
            self.landmarks.mandatory_tasks_lms(model.initial_tn)
            initial_node.lm_node = BitLm_Node()
            initial_node.lm_node.initialize_lms(self.landmarks.mt_lms)
            self.landmarks.identify_lms(self.landmarks.mt_lms, self.landmarks.mt_graph)
        elif self.use_bu_strict:
            self.landmarks =Landmarks(model, True, False, True)
            self.landmarks.generate_mt_table()
            self.landmarks.mandatory_tasks_lms(model.initial_tn)
            self.landmarks.generate_bu_table()
            self.landmarks.bottom_up_lms(model.initial_state, model.initial_tn)
            initial_node.lm_node = BitLm_Node()
            initial_node.lm_node.initialize_lms(self.landmarks.bu_lms-self.landmarks.mt_lms)
            self.landmarks.identify_lms(self.landmarks.bu_lms-self.landmarks.mt_lms, self.landmarks.bu_graph)
        elif self.use_lmc:
            self.landmarks =LMCutRC(model)
            self.landmarks.compute_lms()
            #initial_node.lm_node = LMC_Node()
            initial_node.lm_node = BitLm_Node()
            initial_node.lm_node.initialize_lms(self.landmarks.lms)
        else:
            self.landmarks =Landmarks(model, True, False, False)
            self.landmarks.generate_bu_table()
            self.landmarks.bottom_up_lms(model.initial_state, model.initial_tn)
            initial_node.lm_node = BitLm_Node()
            self.landmarks.identify_lms(self.landmarks.bu_lms, self.landmarks.bu_graph)
            if self.use_ucp:
                self.landmarks.compute_ucp(self.landmarks.bu_lms)
                initial_node.lm_node.initialize_lms(self.landmarks.bu_lms, lm_sum=sum(self.landmarks.ucp_cost))
            else:
                initial_node.lm_node.initialize_lms(self.landmarks.bu_lms)
            
        self.elapsed_time = time.perf_counter() - self.start_time                                     
        
        #mark initial state
        if not self.use_lmc:
            self.abtask_lms   = self.landmarks.count_abtask_lms
            self.operator_lms = self.landmarks.count_abtask_lms
            self.methods_lms  = self.landmarks.count_method_lms
            self.fact_lms     = self.landmarks.count_fact_lms
            self.total_lms    = self.abtask_lms + \
                                self.operator_lms + \
                                self.methods_lms + \
                                self.fact_lms
            if not self.use_ucp:
                for fact_pos in range(initial_node.state.bit_length()):
                    if initial_node.state & (1 << fact_pos) \
                            and initial_node.state & (1 << fact_pos):
                            initial_node.lm_node.mark_lm(fact_pos)
        else: #lmcut doesen't have fact and abstract task landmarks
            self.operator_lms    = self.landmarks.count_operator_lms
            self.methods_lms     = self.landmarks.count_method_lms
            self.disjunction_lms = self.landmarks.count_disjunction_lms
            
            self.total_lms   = self.operator_lms + \
                               self.methods_lms + \
                               self.disjunction_lms

        return super().initialize(model, initial_node.lm_node.lm_value())
        
    def __call__(self, parent_node:HTNNode, node:HTNNode):
        if self.use_lmc:
            # node.lm_node = LMC_Node(parent=parent_node.lm_node)
            # if isinstance(node.task, Operator):
            #     node.lm_node.mark_lm(node.task.global_id)
            # else:
            #     node.lm_node.mark_lm(node.decomposition.global_id)
            node.lm_node = BitLm_Node(parent=parent_node.lm_node)
            if isinstance(node.task, Operator):
                lm_index =  self.landmarks.index_of[node.task.global_id]
            else:
                lm_index = self.landmarks.index_of[node.decomposition.global_id]
                
            for dlm in self.landmarks.appears_in[lm_index]:
                node.lm_node.mark_lm(dlm)
            h_value =  node.lm_node.lm_value()

            super().update_info(h_value)
            return h_value
        
        if self.use_ucp:
            node.lm_node = BitLm_Node(parent=parent_node.lm_node)
            if isinstance(node.task, Operator):
                lm_index =  self.landmarks.index_of[node.task.global_id]
            else:
                lm_index = self.landmarks.index_of[node.decomposition.global_id]
            
            for dlm in self.landmarks.appears_in[lm_index]:
                if node.lm_node.is_active_lm(dlm):
                    lm_cost = self.landmarks.ucp_cost[dlm]
                    node.lm_node.mark_lm(dlm, lm_cost)
            h_value =  node.lm_node.lm_value()
            super().update_info(h_value)
            return h_value
                    
        node.lm_node = BitLm_Node(parent=parent_node.lm_node)
        if self.use_bu_update:
            #self.landmarks.generate_bu_table(node.state, reinitialize=False)
            self.landmarks.bottom_up_lms(node.state, node.task_network, reinitialize=False)
            node.lm_node.update_lms(self.landmarks.bu_lms)
            
        # mark last reached task (also add decomposition here)
        node.lm_node.mark_lm(node.task.global_id)
        # in case there is a change in the state:
        if isinstance(node.task, Operator):
            for fact_pos in range(node.task.add_effects.bit_length()):
                if node.task.add_effects & (1 << fact_pos) \
                    and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
                if self.use_disj:
                    node.lm_node.mark_disjunction(node.state)
            # orderings: deleted facts can reactivate fact landmarks
            if self.use_task_ord \
                and (node.task.del_effects & node.lm_node.mark):  # fact landmark is deleted
                self._deal_with_fact_ordering(node, parent_node)
        else: #otherwise mark the decomposition
            node.lm_node.mark_lm(node.decomposition.global_id)
            # task landmark applied ('delete' task from task network)
            if self.use_fact_ord \
                and (node.task.global_id & node.lm_node.lms): 
                self._deal_with_task_ordering(node, parent_node)
        
            
        h_value =  node.lm_node.lm_value()
        super().update_info(h_value)
        
        return h_value

    # NOTE: DEBUG only
    # def close(self, node):
    #     """
    #     Debugging: Print the unfulfilled disjunctions (by bit index) and
    #     list the component names that appear in each unfulfilled disjunction.
        
    #     This method assumes:
    #     - node.lm_node.lms is the bitmask for all unique landmark indices.
    #     - node.lm_node.mark is the bitmask for the disjunctions that have been achieved.
    #     - self.landmarks.index_of maps component IDs to unique landmark indices.
    #     - self.landmarks.appears_in maps each unique landmark index to a list of disjunction indices 
    #         (i.e. positions in the landmark bitmask) where that landmark appears.
    #     """
    #     complete = node.lm_node.lms    # Bitmask for all unique landmark indices.
    #     marked = node.lm_node.mark     # Bitmask for achieved disjunctions.
    #     num_disj = complete.bit_length()

    #     # Build an inverse mapping: unique index -> list of component IDs.
    #     inverse_index = {}
    #     for comp_id, uid in self.landmarks.index_of.items():
    #         inverse_index.setdefault(uid, []).append(comp_id)

    #     print("=== Unfulfilled Disjunctions and their Components ===")
    #     # Iterate over each disjunction index (bit position).
    #     for disj in range(num_disj):
    #         # If this disjunction is not achieved:
    #         if not (marked & (1 << disj)):
    #             print(f"Disjunction {disj} not achieved:")
    #             # Look for all unique landmark indices that appear in this disjunction.
    #             for uid, disj_list in self.landmarks.appears_in.items():
    #                 if disj in disj_list:
    #                     # For each unique landmark, list all the corresponding component IDs.
    #                     if uid in inverse_index:
    #                         for comp_id in inverse_index[uid]:
    #                             comp = self.model.get_component(comp_id)
    #                             print(f"\tComponent {comp_id}: {comp.name}")



        


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

    def __repr__(self):
        options = []
        if self.use_task_ord:
            options.append("use_task_ord")
        if self.use_fact_ord:
            options.append("use_fact_ord")
        if self.use_bid:
            options.append("use_bid")
        if self.use_bu_update:
            options.append("use_bu_update")
        
        options_str = ", ".join(options)
        return f'lmcount({options_str})' if options else 'lmcount()'

    def __str__(self):
        options = []
        if self.use_task_ord:
            options.append("use_task_ord")
        if self.use_fact_ord:
            options.append("use_fact_ord")
        if self.use_bid:
            options.append("use_bid")
        if self.use_bu_update:
            options.append("use_bu_update")
        
        options_str = ", ".join(options)
        return f'lmcount({options_str})' if options else 'lmcount()'

    def __output__(self):
        # Get the singleton instance of Descriptions
        desc = Descriptions()

        out_str = f'Heuristic Info:\n'
        out_str += f'\t{desc("heuristic_name", self.name)}\n'
        out_str += f'\t{desc("total_landmarks", self.total_lms)}\n'
        out_str += f'\t{desc("operator_landmarks", self.operator_lms)}\n'
        out_str += f'\t{desc("abtask_landmarks", self.abtask_lms)}\n'
        out_str += f'\t{desc("method_landmarks", self.methods_lms)}\n'
        out_str += f'\t{desc("fact_landmarks", self.fact_lms)}\n'
        out_str += f'\t{desc("disj_landmarks", self.disjunction_lms)}\n'
        out_str += f'\t{desc("fact_reactivations", self.fact_lm_reactivations)}\n'
        out_str += f'\t{desc("task_reactivations", self.fact_lm_reactivations)}\n'
        out_str += f'\t{desc("heuristic_elapsed_time", f"{self.elapsed_time:.4f}")}\n'
        
        
        return out_str