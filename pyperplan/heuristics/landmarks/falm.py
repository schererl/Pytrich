from collections import deque
from copy import deepcopy
import gc

from pyperplan.heuristics.landmarks.landmark import Landmarks
from pyperplan.model import Operator

class FALM:
    def __init__(self, model, lms_instance=None):
        self.model=model
        self.ord_to_op = {}
        self.opid_to_ord = {}
        self.fact_to_ord = {}
        self.unique_achievers = []
        
        if lms_instance:
            self.andor_lm_inst  = lms_instance
            self.andor_landmark_set = lms_instance.task_lms | lms_instance.fact_lms | lms_instance.method_lms
        else:            
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

    def _calculate_reachable(self):
        """
        Calculate the reachable set of actions for each task, both primitive and compound.
        """
        # Initialize reachable for all tasks
        self.reachable = {task.global_id: set() for task in self.model.abstract_tasks + self.model.operators}
        
        # Initialize reachable for primitive actions
        for action in self.model.operators:
            self.reachable[action.global_id] = {action.global_id}
        
        # Calculate reachable for compound tasks using DFS
        for task in self.model.abstract_tasks:
            reachable_set = set()
            self._dfs(task, reachable_set, visited=set())
            self.reachable[task.global_id] = deepcopy(reachable_set)
            

    def _dfs(self, task, reachable, visited):
        """
        Perform a depth-first search to find all reachable tasks for a compound task.
        
        Args:
            task (int): The task ID for which to compute the reachable set.
            visited (set): Set of visited tasks to prevent cycles.
        """
        if task in visited:
            return
        
        visited.add(task)

        if self.reachable[task.global_id]:
            reachable.update(self.reachable[task.global_id])
        
        for decomposition in task.decompositions:
            for subtask in decomposition.task_network:
                if subtask in self.model.operators:  # If subtask is a primitive action
                    reachable.add(subtask.global_id)
                else:  # If subtask is a compound task
                    self._dfs(subtask, reachable, visited)

    def _output_reachable(self):
        for task in self.model.abstract_tasks:
            print(f'{task.name} A {len(self.reachable[task.global_id])}.')
            for r in self.reachable[task.global_id]:
               print(f'\t{self.model.get_component(r).name}')

    def _calculate_predecessors(self):
        """
        Calculate the predecessor actions for each action in the set of actions A.
        
        Modifies:
            self.predecessors: A dictionary where keys are action indices, and values are sets of predecessor actions.
        """
        self.predecessors = {a.global_id: set() for a in self.model.operators}
        
        # Iterate through each method
        for decomposition in self.model.decompositions:
            subtasks = decomposition.task_network
            
            for i in range(len(subtasks)):
                task_i = subtasks[i].global_id
                for action_id in self.reachable[task_i]:
                    for j in range(i - 1, -1, -1):
                        task_j = subtasks[j].global_id
                        self.predecessors[action_id].update(self.reachable[task_j])
        
        # Iterate through task network
        subtasks = self.model.initial_tn
        for i in range(len(subtasks)):
            task_i = subtasks[i].global_id
            for action_id in self.reachable[task_i]:
                for j in range(i - 1, -1, -1):
                    task_j = subtasks[j].global_id
                    self.predecessors[action_id].update(self.reachable[task_j])

    def _check_oplms_achievers(self):
        for lm_id in self.andor_landmark_set:
            component = self.model.get_component(lm_id)
            if isinstance(component, Operator):
                print(f'landmark refinable: ')
                self._check_predecessor_achievers(lm_id)

    def _check_all_hierachy_achievers(self):
        for operator in self.model.operators:
            self._check_predecessor_achievers(operator.global_id)

    def _compute_precon_intesection(self, achievers, fact_set):
            disjunctive_landmarks = [set(self.model.get_component(op_id).get_precons_bitfact()) for op_id in achievers]
            # Get the intersection of disjunctive landmarks
            if disjunctive_landmarks:
                interesection_lms = set.intersection(*disjunctive_landmarks)
                fact_set.update(interesection_lms)

    def _compute_andor_intesection(self, achievers, lm_set):
            disjunctive_landmarks = [set(self.andor_lm_inst.bu_landmarks[op_id]) for op_id in achievers]
            # Get the intersection of disjunctive landmarks
            if disjunctive_landmarks:
                interesection_lms = set.intersection(*disjunctive_landmarks)
                lm_set.update(interesection_lms)
            
                    

    def _check_predecessor_achievers(self, operator_id):
        """
        Check if the achievers of an operator by their predecessors
        are smaller than the overall predecessor collection.
        """
        
        operator = self.model.get_component(operator_id)
        preconditions = operator.get_precons_bitfact()
        if operator.relaxed_applicable_bitwise(self.model.initial_state):
            #print(f'\n{operator.name} trivially reachable')
            return set()
        
        # Overall achievers: operators that have effects matching the preconditions
        overall_achievers = set()
        for precon in preconditions:
            overall_achievers.update(
                o.global_id for o in self.model.operators if o.add_effects_bitwise & (1 << precon) != 0
            )
        
        # Predecessor achievers: operators that are predecessors and achieve the preconditions
        predecessor_achievers = set()
        preconditions = operator.get_precons_bitfact()
        for precon in preconditions:
            predecessor_achievers.update(
                o_id for o_id in self.predecessors[operator_id] if ((self.model.get_component(o_id).add_effects_bitwise) & (1 << precon) != 0)
            )

        # Check if the predecessor achievers are smaller
        if len(predecessor_achievers) < len(overall_achievers):
            print(f"\nOperator {operator.name}: {len(predecessor_achievers)}/{len(overall_achievers)}")
            #if len(predecessor_achievers) == 0:
            #    print(f"\nOperator {operator.global_id}:  {len(predecessor_achievers)}/{len(overall_achievers)}")
                #print(f"Predecessor Achievers: {len([self.model.get_component(o_id).name for o_id in predecessor_achievers])}")
                #print(f"Overall Achievers: {len([self.model.get_component(o_id).name for o_id in overall_achievers])}")
        
            if not self._test_applicable(predecessor_achievers, operator):
                print(f'operator not applicable {operator.name}')
            

        
        # compute the intersection of facts of overral_achievers
        overall_precons = set()
        self._compute_andor_intesection(overall_achievers, overall_precons)
        # compute the intersection of facts of predecessors_achievers
        predec_precons = set()
        # check if the intersection of prededc achievers is higher
        self._compute_andor_intesection(predecessor_achievers, predec_precons)
        if predec_precons - overall_precons:
            #print(overall_precons)
            #print(predec_precons)
            for lm in predec_precons - overall_precons:
                if not lm in self.andor_lm_inst.bu_landmarks[operator_id]:
                    component = self.model.get_component(lm)
                    if isinstance(component, int):
                        print(f'{self.model.get_fact_name(lm)}')
                    else:
                        print(component.name)
        return predecessor_achievers


    def _test_applicable(self, achievers, op):
        s = self.model.initial_state
        for a in achievers:
            a_o = self.model.get_component(a)
            s = a_o.relaxed_apply_bitwise(s)
        return op.applicable_bitwise(s)

    def _output_predecessors(self):
        for o in self.model.operators:
            print(f'{o.name} A {len(self.predecessors[o.global_id])}.')
            #for p in self.predecessors[o.global_id]:
            #   print(f'\t{self.model.get_component(p).name}')

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
                    
        self._log_andor_landmarks()
        self._log_gord_landmarks()

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
        # OPTION 2: get landmarks of each operator disjunction
        td_landmarks = [set(self.andor_lm_inst.bu_landmarks[op_id]) for op_id in operators_disjunction]
        if td_landmarks:
            interesection_lms = set.intersection(*td_landmarks)
            for lm in interesection_lms:
                if lm not in self.andor_landmark_set:
                    self.landmark_set |= self.andor_lm_inst.bu_landmarks[lm]  | self.andor_lm_inst.td_landmarks[lm]

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