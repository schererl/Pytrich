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
        self.ord_to_fact = {}
        self.unique_achievers = []
        
        self.andor_lm_inst  = Landmarks(self.model)
        self.andor_lm_inst.bottom_up_lms()
        self.andor_lm_inst.top_down_lms()
        self.andor_landmark_set = self.andor_lm_inst.bidirectional_lms(self.model, self.model.initial_state, self.model.initial_tn)

        self.valid_disjunctions = []

    def _calculate_op_achievers(self):
        self.landmark_set = set() #landmarks 0 1 and 2 
        for fact in range(len(bin(self.model.goals))-2):
            if self.model.goals & (1 << fact) != 0:
                self.landmark_set.add(fact)
                
        if not self.landmark_set:
            print(f'ANY TRIVIAL LANDMARKS FOUND, ADDING AND-OR-GRAPH LANDMARKS')
            self.landmark_set |= self.andor_landmark_set
        
        
        changed = True
        while changed:
            changed=False
            for fact, order in self.ord_to_fact.items():
                if not fact in self.landmark_set or order==0:
                    continue
                
                # print(f'fact {fact}: {self.model.get_fact_name(fact)} ord {order}')
                fact_achievers = set()
                
                all_achievers_count = 0
                for o in self.model.operators:
                    if (1 << fact) & o.add_effects_bitwise != 0:
                        all_achievers_count+=1
                
                for o_a in self.ord_to_op[order-1]: # only operators from immediate last step
                    if (1 << fact) & o_a.add_effects_bitwise != 0: # check if o_a is achiever of the fact
                        #print(f'\tACHIEVE {o_a.name}')
                        fact_achievers.add(o_a.global_id)
                
                if fact_achievers:
                    #print(f'fact {fact}: {self.model.get_fact_name(fact)} ord {order}')
                    #print(f'\tNEW LMS: {unique_fact_achievers}')
                    unique = True
                    for ua in self.unique_achievers:
                        if ua == fact_achievers:
                            unique=False
                            break
                        
                            
                    if unique:
                        self.unique_achievers.append(fact_achievers)
                        if len(fact_achievers) == 1:
                            # new operator
                            o_id = next(iter(fact_achievers))
                            if o_id not in self.landmark_set:
                                print(f'lm {o_id}: {self.model.get_component(o_id).name}')
                                self.landmark_set.add(o_id)
                                # every precontition is a new landmark
                                for fact in self.model.get_component(o_id).get_precons_bitfact():
                                    self.landmark_set.add(fact)
                        else:
                            # found a disjunction, find out if there is a interesection of fact's predicates
                            # also add the disjuction of operators as a new landmark (only if it is relevant)
                            self._compute_intersection(fact_achievers, all_achievers_count)
                        changed |= True
                        

        print(f'greedy lms: {sorted(self.landmark_set)}')
        print(f'andor lms: {sorted(self.andor_landmark_set)}')
        print(f'new lms {set(self.landmark_set)-set(self.andor_landmark_set)}')
        
        for newlm in set(self.landmark_set)-set(self.andor_landmark_set):
            component = self.model.get_component(newlm)
            if isinstance(component, Operator):
                for fact_lm in component.get_precons_bitfact():
                    print(f'{fact_lm}', end=' ')

        for newlm in set(self.landmark_set)-set(self.andor_landmark_set):
            for more_new_lm in self.andor_landmark_set:
                if more_new_lm not in self.andor_landmark_set:
                    print(f'MORE {more_new_lm}', end=' ')
        
        print('')
        print(f'valid disjunctions: {self.valid_disjunctions}')
        for vd in self.valid_disjunctions:
            print(f'disjunction:')
            for lm in vd:
                print(f'\t{self.model.get_component(lm).name}')

        #exit(0)
    
    def _compute_intersection(self, operators_disjunction, all_achievers_count):
        # Consider the disjunction of operators as a new landmarks in case is RELEVANT
        # RELEVANT: at most 4 operators and the greedy-ordering for the given fact landmark is not the fully achievable set of operators
        if len(operators_disjunction) <= 4 and len(operators_disjunction) < all_achievers_count:
            self.valid_disjunctions.append(operators_disjunction)
        
        
        # OPTION 1: fact preconditions for operator disjunction
        disjunctive_landmarks = [set(self.model.get_component(op_id).get_precons_bitfact()) for op_id in operators_disjunction]
        # OPTION 2: get landmarks of each operator disjunction
        #disjunctive_landmarks = [set(self.landmarks.bu_landmarks[op_id]) for op_id in operators_disjunction]

        # Get the intersection of disjunctive landmarks
        if disjunctive_landmarks:
            interesection_lms = set.intersection(*disjunctive_landmarks)
            for lm in interesection_lms:
                if lm not in self.landmark_set:
                    #print(f'New landmark from intersection {f}: {self.model.get_fact_name(f)}')
                    self.landmark_set.add(lm)
        
        # OPTION 2: get landmarks of each operator disjunction
        td_landmarks = [set(self.andor_lm_inst.td_landmarks[op_id]) for op_id in operators_disjunction]
        print(f'td_landmarks {td_landmarks}\n')
        if td_landmarks:
            interesection_lms = set.intersection(*td_landmarks)
            print(f'INTERSECTION> {interesection_lms}')
            for lm in interesection_lms:
                if lm not in self.andor_landmark_set:
                    if not isinstance(self.model.get_component(lm), int):
                        print(f'New landmark {self.model.get_component(lm).name}')
                    else:
                        print(f'fact {lm}')

        print(f'')
                    

        
        

                                

    def segment_operators(self):
        
        acc_O = set()
        O = []

        change=True
        it = 0
        
        S = [self.model.initial_state]
        for f_a in range(len(bin(self.model.initial_state))-2):
            if self.model.initial_state & (1 << f_a):
                self.ord_to_fact[f_a] = it

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
                    self.ord_to_fact[f_a] = it
                    #print(f'new fact {f_a} => {it}')
        
        self._calculate_op_achievers()
        