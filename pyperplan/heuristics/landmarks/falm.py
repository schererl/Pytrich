from collections import deque
from copy import deepcopy
import gc

from pyperplan.heuristics.landmarks.landmark import Landmarks
from pyperplan.model import Operator

class FALM:
    def __init__(self, model):
        self.model=model
        self.ord_to_op = {}
        self.opid_to_ord = {}
        self.fact_to_ord = {}
        self.unique_achievers = []
        
        self.andor_lm_inst  = Landmarks(self.model)
        self.andor_lm_inst.bottom_up_lms()
        self.andor_lm_inst.top_down_lms()
        self.andor_landmark_set = self.andor_lm_inst.bidirectional_lms(self.model, self.model.initial_state, self.model.initial_tn)

        self.valid_disjunctions = []

    def _log_andor_landmarks(self):
        count_op_lms   = 0
        count_fact_lms = 0
        for lm in self.andor_landmark_set:
            component = self.model.get_component(lm)
            if isinstance(component, int):
                count_fact_lms+=1
            elif isinstance(component, Operator):
                count_op_lms+=1
        count_total_lms = count_fact_lms + count_op_lms
        print(f'and-or landmark operators: {count_op_lms}')
        print(f'and-or landmark facts: {count_fact_lms}')
        print(f'and-or landmark total: {count_total_lms}')

    def _log_gord_landmarks(self):
        count_op_lms   = 0
        count_fact_lms = 0
        for lm in self.landmark_set:
            component = self.model.get_component(lm)
            if isinstance(component, int):
                count_fact_lms+=1
            elif isinstance(component, Operator):
                count_op_lms+=1
        count_total_lms = count_fact_lms + count_op_lms
        print(f'gord landmark operators: {count_op_lms}')
        print(f'gord landmark facts: {count_fact_lms}')
        print(f'gord landmark total: {count_total_lms}')
        print(f'gord landmark disjunctions: {len(self.valid_disjunctions)}')

    # greedy-necessary before landmarks
    def _compute_gnb_landmarks(self):
        # self.landmark_set = set() #landmarks 0 1 and 2 
        # for fact in range(len(bin(self.model.goals))-2):
        #     if self.model.goals & (1 << fact) != 0:
        #         self.landmark_set.add(fact)
                
        # if not self.landmark_set:
        #     print(f'ANY TRIVIAL LANDMARKS FOUND, ADDING AND-OR-GRAPH LANDMARKS')
        
        self.landmark_set = deepcopy(self.andor_landmark_set)
        lm_queue = deque()
        for lm in self.landmark_set:
            if isinstance(self.model.get_component(lm), int):
                lm_queue.append(lm)
        
        while lm_queue:
            lm_fact = lm_queue.popleft()
            order = self.fact_to_ord[lm_fact]
            if order == 0:
                continue
            # print(f'trying landmarks: {self.model.get_fact_name(lm_fact)}')
            possibly_achievers = set()
            
            #for o_a in self.ord_to_op[order-1]: # only operators from immediate last step
            for o_a in self.model.operators:
            #for o_a in self._compute_pb_achievers(lm_fact):
                if  o_a.add_effects_bitwise & (1 << lm_fact) != 0: # check if o_a is achiever of the fact
                    possibly_achievers.add(o_a.global_id)
            
            if possibly_achievers:
                all_achievers_count = sum(1 for o in self.model.operators if o.add_effects_bitwise & (1 << lm_fact) != 0)
                # print(f'\tfound greedy achievers {len(greedy_achievers)}/{all_achievers_count}')
                unique = all(possibly_achievers != ua for ua in self.unique_achievers)
                if unique:
                    self.unique_achievers.append(possibly_achievers)
                    self._compute_intersection(lm_queue, possibly_achievers, all_achievers_count)
                    
                        

        #print(f'greedy lms: {sorted(self.landmark_set)}')
        #print(f'andor lms: {sorted(self.andor_landmark_set)}')
        # new_landmarks = set(self.landmark_set)-set(self.andor_landmark_set)
        # if new_landmarks:
        #     print(f'new lms {new_landmarks}')
        self._log_andor_landmarks()
        self._log_gord_landmarks()
        #exit()

        
    def _compute_intersection(self, lm_queue, operators_disjunction, all_achievers_count):
        if len(operators_disjunction) == 1:
            # new operator
            o_id = next(iter(operators_disjunction))
            if o_id not in self.landmark_set:
                self.landmark_set.add(o_id)
            # every precontition is a new landmark
            for fact in self.model.get_component(o_id).get_precons_bitfact():
                if fact not in self.landmark_set:
                    # print(f'NL {self.model.get_fact_name(fact)}')
                    self.landmark_set.add(fact)
                    lm_queue.append(fact)
            return
        
        # Consider the disjunction of operators as a new landmarks in case is RELEVANT
        # RELEVANT: at most 4 operators and the greedy-ordering for the given fact landmark is not the fully achievable set of operators
        if len(operators_disjunction) <= 4 and len(operators_disjunction) < all_achievers_count:
            self.valid_disjunctions.append(operators_disjunction)
        
        # OPTION 1: fact preconditions for operator disjunction
        disjunctive_landmarks = [set(self.model.get_component(op_id).get_precons_bitfact()) for op_id in operators_disjunction]
        # Get the intersection of disjunctive landmarks
        if disjunctive_landmarks:
            interesection_lms = set.intersection(*disjunctive_landmarks)
            if interesection_lms:
                for lm in interesection_lms:
                    if lm not in self.landmark_set:
                        self.landmark_set.add(lm)
                        if isinstance(self.model.get_component(lm), int):
                            #print(f'NL {self.model.get_fact_name(lm)}')
                            lm_queue.append(lm)
            else:
                minimal_disj = self._compute_minimal_fact_disjunction(operators_disjunction, disjunctive_landmarks)
                if minimal_disj not in self.valid_disjunctions:
                    self.valid_disjunctions.append(minimal_disj)
        
        # OPTION 2: get landmarks of each operator disjunction
        td_landmarks = [set(self.andor_lm_inst.td_landmarks[op_id]) for op_id in operators_disjunction]
        if td_landmarks:
            interesection_lms = set.intersection(*td_landmarks)
            for lm in interesection_lms:
                if lm not in self.andor_landmark_set:
                    self.landmark_set |= self.andor_lm_inst.bu_landmarks[lm]  | self.andor_lm_inst.td_landmarks[lm]

    def _compute_minimal_fact_disjunction(self, disj_operators, disj_precons):
        """
        This function finds a minimal set of fact preconditions that covers all operators in the disjunction.
        """
        minimal_facts = set()
        all_facts = set.union(*disj_precons)
        
        fact_coverage = {fact: set() for fact in all_facts}
        for op_disj_i, op in enumerate(disj_operators):
            for fact in disj_precons[op_disj_i]:
                fact_coverage[fact].add(op)
        # keep track of covered operators
        covered_operators = set()
        num_operators = len(disj_operators)
        # greedy approach: select facts that cover the most uncovered operators
        # NOTE: I think it is not optimal
        while len(covered_operators) < num_operators:
            # find the fact that covers the most uncovered operators
            best_fact = max(fact_coverage, key=lambda f: len(fact_coverage[f] - covered_operators))
            best_coverage = fact_coverage[best_fact] - covered_operators
            # add this fact to the minimal set
            minimal_facts.add(best_fact)
            # mark these operators as covered
            covered_operators.update(best_coverage)
            # remove the best fact from future consideration
            del fact_coverage[best_fact]
        
        
        
        return minimal_facts

    # operators applicable possibly-before B
    def _compute_pb_achievers(self, lm_fact):
        current_state = self.model.initial_state
        excluded_ops = {o for o in self.model.operators if (1 << lm_fact) & o.add_effects_bitwise != 0}
        
        relaxed_graph = [current_state]
        applicable_ops = set(self.model.operators) - excluded_ops
        new_facts = current_state
        
        while True:
            next_facts = new_facts
            for o in applicable_ops:
                if o.relaxed_applicable_bitwise(next_facts):
                    next_facts = o.relaxed_apply_bitwise(next_facts)
            
            if next_facts == relaxed_graph[-1]:
                break
            relaxed_graph.append(next_facts)
            new_facts = next_facts

        pb_facts = relaxed_graph[-1]
        pb_achievers = {o for o in self.model.operators if o.relaxed_applicable_bitwise(pb_facts) and (1 << lm_fact) & o.add_effects_bitwise != 0}
        return pb_achievers

    # over-approximation for first achievers
    def _compute_ft_achievers(self):
        acc_O = set()
        O = []

        change=True
        it = 0
        
        S = [self.model.initial_state]
        for f_a in range(len(bin(self.model.initial_state))-2):
            if self.model.initial_state & (1 << f_a):
                self.fact_to_ord[f_a] = it
                

        while change:
            current_state = S[-1]
            applicable_ops = {o for o in self.model.operators if o.relaxed_applicable_bitwise(current_state)} - acc_O
            if not applicable_ops:
                break

            self.ord_to_op[it] = []
            for o in applicable_ops:
                self.ord_to_op[it].append(o)
                self.opid_to_ord[o.global_id] = it

            acc_O |= applicable_ops
            O.append(applicable_ops)
            new_state = deepcopy(current_state)
            for op in applicable_ops:
                new_state = op.relaxed_apply_bitwise(new_state)
            S.append(new_state)
            it+=1

            unique_facts = new_state & (new_state ^ current_state)
            for f_a in range(len(bin(unique_facts))-2):
                if unique_facts & (1 << f_a):
                    self.fact_to_ord[f_a] = it
                    #print(f'new fact {f_a} => {it}')
        
    def extract_landmarks(self):
        self._compute_ft_achievers()
        self._compute_gnb_landmarks()