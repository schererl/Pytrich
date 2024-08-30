from collections import deque
from copy import deepcopy
import gc

from Pyperplan.ProblemRepresentation.and_or_graphs import AndOrGraph
from Pyperplan.ProblemRepresentation.and_or_graphs import NodeType
from Pyperplan.ProblemRepresentation.and_or_graphs import ContentType
from Pyperplan.model import Model

# store landmarks, needed when landmarks are updated for each new node
class LM_Node:
    def __init__(self, parent=None):
        if parent:
            self.lms = parent.lms
            self.mark = parent.mark
            self.number_lms = parent.number_lms
            self.achieved_lms = parent.achieved_lms
            
            self.disjunctions = deepcopy(parent.disjunctions)
            self.number_disj   = parent.number_disj
            self.achieved_disj = parent.achieved_disj
        else:
            self.lms  = 0
            self.mark = 0
            self.number_lms   = 0   # total number of lms
            self.achieved_lms = 0   # total achieved lms

            self.disjunctions = set()
            self.number_disj   = 0
            self.achieved_disj = 0
            
    # mark as 'achieved' if node is a lm
    def mark_lm(self, node_id):
        if self.lms & (1 << node_id) and ~self.mark & (1 << node_id):
            self.mark |= 1 << node_id
            self.achieved_lms+=1
        
    # add new lms
    def update_lms(self, new_lms):
        for lm_id in new_lms:
            if ~self.lms & (1 << lm_id):
                self.lms |= (1 << lm_id)
                self.number_lms+=1
    
    # add new disjunctions
    # each disjunction corresponds to a single fact
    # so each disjunction formula is an integer, instead of a set of ints
    def update_disjunctions(self, new_disj):
        for disj in new_disj:
            bit_disj = 0
            for lm in disj:
                bit_disj |=  1 << lm
            self.disjunctions.add(bit_disj)
            self.number_disj+=1
    
    def mark_disjunction(self, state):
        """
        Check if any disjunction is satisfied.
        A disjunction is satisfied if its bitwise AND with `fact` is non-zero.
        """
        to_remove = set()
        for disj in self.disjunctions:
            if disj & state != 0:
                self.achieved_disj += 1
                to_remove.add(disj)
                
        # remove every element from self.disjunctions
        self.disjunctions = self.disjunctions - to_remove


    def lm_value(self):
        return self.number_lms - self.achieved_lms + self.number_disj - self.achieved_disj
    
    def get_unreached_landmarks(self):
        unreached = []
        for i in range(len(bin(self.lms))-2):
            if self.lms & (1 << i) and not self.mark & (1 << i):
                unreached.append(i)
        return unreached

    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlms: {bin(self.lms)}\n\tachieved: {bin(self.mark)}\n{self.achieved_disj}/{self.number_disj}"

class Landmarks:
    def __init__(self, model:Model, bidirectional=True):
        self.model=model
        self.bidirectional=bidirectional
        self.bu_AND_OR     = AndOrGraph(model, use_top_down=False) # bottom-up and or graph
        self.len_landmarks = len(self.bu_AND_OR.nodes)
        self.bu_landmarks  = [None] * self.len_landmarks # bottom-up landmarks
        
        if bidirectional:
            self.td_AND_OR = AndOrGraph(model, use_top_down=True)  # top-down and or graph
            self.td_landmarks    = [set()] * self.len_landmarks # top-down landamarks

        self.task_lms = set()
        self.fact_lms = set()
        self.method_lms = set()
        self.valid_disjunctions = []
        
    def _compute_minimal_fact_disjunction(self, disj_operators, disj_precons, TA):
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
        # greedy approach: select facts that cover the most uncovered operators
        while len(covered_operators) < TA and fact_coverage:
            # find the fact that covers the most uncovered operators
            best_fact = max(fact_coverage, key=lambda f: len(fact_coverage[f] - covered_operators))
            best_coverage = fact_coverage[best_fact] - covered_operators
            # add this fact to the minimal set
            minimal_facts.add(best_fact)
            # mark these operators as covered
            covered_operators.update(best_coverage)
            # remove the best fact from future consideration
            del fact_coverage[best_fact]
        
        # if it is not possible cover all return set()
        if len(covered_operators) < TA:
            return set()

        # remove facts used into minimal facts from each disjunction 
        for i, precon_set in enumerate(disj_precons):
            disj_precons[i] = precon_set - minimal_facts
        return minimal_facts
    
    def _compute_minimal_disjunctions(self):
        for lm_fact in self.fact_lms:
            o_achievers = set()
            for o_a in self.model.operators:
                if  o_a.add_effects_bitwise & (1 << lm_fact) != 0:
                    o_achievers.add(o_a)
            # OPTION 1: fact preconditions for operator disjunction
            disjunctive_preconitions = [set(o_a.get_precons_bitfact()) for o_a in o_achievers]
            # Get the intersection of disjunctive landmarks
            if disjunctive_preconitions:
                interesection_lms = set.intersection(*disjunctive_preconitions)
                if not interesection_lms:
                    
                    # compute maximal minimal disjunctions
                    total_achievers = len(o_achievers)
                    while disjunctive_preconitions:
                        minimal_disj = self._compute_minimal_fact_disjunction(o_achievers, disjunctive_preconitions, total_achievers)
                        if not minimal_disj or len(minimal_disj) > 4:
                            break
                        if  minimal_disj not in self.valid_disjunctions:
                            self.valid_disjunctions.append(minimal_disj)
                            
    def bottom_up_lms(self):
        """
        Original landmark extraction:
          We refer to it as 'bottom-up landmarks' because it captures the HTN hierarchy this way
          see: Höller, D., & Bercher, P. (2021). Landmark Generation in HTN Planning. Proceedings of the AAAI Conference on Artificial Intelligence
        """
        queue = deque([node for node in self.bu_AND_OR.nodes if len(node.predecessors) == 0])
        while queue:
            node = queue.popleft()
            new_landmarks= None
            pred_lms = []
            all_lms= False
            for pred in node.predecessors:
                lms = self.bu_landmarks[pred.ID]
                if lms is None:
                    all_lms=True
                    continue
                pred_lms.append(self.bu_landmarks[pred.ID])
            
            if node.type == NodeType.OR and node.predecessors:
                # in case of some predecessor had all landmarks, just ignore it and apply the interesection of the others
                if len(pred_lms) >= 1:
                    new_landmarks = set.intersection(*(pred_lms)) | {node.ID}
                
            elif node.type == NodeType.AND and node.predecessors:
                # if some predecessor had all landmarks, consider node containing all landmarks also
                if not all_lms:
                    new_landmarks = set.union(*(pred_lms)) | {node.ID}
            else:
                new_landmarks = {node.ID}
            
            if  new_landmarks != self.bu_landmarks[node.ID]:
                self.bu_landmarks[node.ID] = new_landmarks
                for succ in node.successors:
                    queue.append(succ)

                
                
    def top_down_lms(self):
        """
        top-down landmarks extraction, our proposed works:
            (1) use a AND OR graph with inverted arcs at tasks and methods -operators and facts are the same
            (2) considering 'Operator' nodes as a sort of a hybrid node: for facts its 'AND' node, for methods its an 'OR' node.
            (3) extract landmarks using this graph.
        """
        if not self.bidirectional:
            raise ValueError("Bidirectional flag set to false, top-down landmarks not allowed")
        
        queue = deque([node for node in self.td_AND_OR.nodes if len(node.predecessors) == 0])
        while queue:
            node = queue.popleft()
            new_landmarks= None
            # operators are 'and' nodes for facts and 'or' nodes for methods
            # the landmarks got from the intersection of methods are added to landmarks got from facts.
            if node.content_type == ContentType.OPERATOR and node.predecessors:
                method_lms = []
                method_all_lms = False
                fact_lms = []
                fact_all_lms = False
                for pred in node.predecessors:
                    lms = self.td_landmarks[pred.ID]
                    if pred.content_type == ContentType.METHOD:
                        if lms is None:
                            method_all_lms=True
                            continue
                        method_lms.append(self.td_landmarks[pred.ID])
                    else:
                        if lms is None:
                            fact_all_lms=True
                            continue
                        fact_lms.append(self.td_landmarks[pred.ID])

                # if all landmarks are reachable from facts or methods ('none' value), there is nothing to do
                #TODO: here is a little tricky, maybe improve
                if fact_all_lms or method_all_lms: # found a predecessor not ready (all lms marked)
                    new_landmarks=None
                else:
                    if len(method_lms) == 0:
                        method_lms = [set()] # no method has the operator as subtasks -initial task network exclusive
                    if len(fact_lms) == 0:
                        fact_lms = [set()]   # no preconditions
                    new_landmarks = set.intersection(*(method_lms)).union(*(fact_lms)).union({node.ID})
                    
            else: #else behaves normally
                pred_lms = []
                all_lms= False
                for pred in node.predecessors:
                    lms = self.td_landmarks[pred.ID]
                    if lms is None:
                        all_lms=True
                        continue
                    pred_lms.append(self.td_landmarks[pred.ID])
                if node.type == NodeType.OR and node.predecessors:
                    if len(pred_lms) >= 1:
                        new_landmarks = set.intersection(*(pred_lms)) | {node.ID}
                elif node.type == NodeType.AND and node.predecessors:
                    if not all_lms:
                        new_landmarks = set.union(*(pred_lms)) | {node.ID}
                else:
                    new_landmarks = {node.ID}
            
            if  new_landmarks != self.td_landmarks[node.ID]:
                self.td_landmarks[node.ID] = new_landmarks
                for succ in node.successors:
                    queue.append(succ)

        
    def bidirectional_lms(self, state, task_network):
        """
        Combination of bottom-up landmarks w/ top-down landmarks:
            - refine operators found by bottom-up landmarks using top-down landmarks
            - refine methods found by top-down landmarks using bottom-up landamrks
            - repeat until exausting every possible refinment 
        Args:
            model (Model): The planning model.
            state (int): Bitwise representation of the current state.
            task_network (list): List of tasks in the task network.

        Returns:
            set: Set of computed landmarks.
        """
        if not self.bidirectional:
            raise ValueError("Bidirectional flag set to false, bidirectional landmark extraction not allowed")
        # get classical landmarks for the given problem
        landmarks = set()
        # compute landmarks based on the initial state and goal conditions
        for fact_pos in range(len(bin(self.model.goals))-2):
            if self.model.goals & (1 << fact_pos) and ~state & (1 << fact_pos):
                for lm in self.bu_landmarks[fact_pos]:
                    landmarks.add(lm)
                    
        
        # compute landmarks based on task network
        for t in task_network:
            for lm in self.bu_landmarks[t.global_id]:
                landmarks.add(lm)
        
        visited   = set()
        queue = deque()  # Ensure queue is a deque
        queue.extend([lm for lm in landmarks])  # Use extend to add elements to the deque
        
        # iterate over each landmark and increment with td and bu landmarks while new landarks are discovered
        while queue:
            node_id = queue.popleft()
            visited.add(node_id)
            landmarks.add(node_id)
            # top-down landmarks
            for lm_id in self.td_landmarks[node_id]:
               if not lm_id in visited:
                   queue.append(lm_id)
            # bottom-up landmarks
            for lm_id in self.bu_landmarks[node_id]:
                if not lm_id in visited:
                    queue.append(lm_id)
        
        for lm_id in landmarks:
            if self.bu_AND_OR.nodes[lm_id].content_type == ContentType.FACT:
                self.fact_lms.add(lm_id)
            elif self.bu_AND_OR.nodes[lm_id].content_type == ContentType.METHOD:
                self.method_lms.add(lm_id)
            else:
                self.task_lms.add(lm_id)
        # print(f'bidirectional')
        # print([self.bu_AND_OR.nodes[id] for id in landmarks])
        # print(len([self.bu_AND_OR.nodes[id] for id in landmarks]))
        # self._calculate_fact_achievers(20)
        
        return landmarks
    
    def classical_lms(self, state, task_network):
        landmarks = set()
        # compute landmarks based on the initial state and goal conditions
        for fact_pos in range(len(bin(self.model.goals))-2):
            if self.model.goals & (1 << fact_pos) and ~state & (1 << fact_pos):
                for lm in self.bu_landmarks[fact_pos]:
                    landmarks.add(lm)
        # compute landmarks based on task network
        for t in task_network:
            for lm in self.bu_landmarks[t.global_id]:
                landmarks.add(lm)
        
        for lm_id in landmarks:
            if self.bu_AND_OR.nodes[lm_id].content_type == ContentType.FACT:
                self.fact_lms.add(lm_id)
            elif self.bu_AND_OR.nodes[lm_id].content_type == ContentType.METHOD:
                self.method_lms.add(lm_id)
            else:
                self.task_lms.add(lm_id)
        # print('classical')
        # print([self.bu_AND_OR.nodes[id] for id in landmarks])
        # print(len([self.bu_AND_OR.nodes[id] for id in landmarks]))
        # exit()
        return landmarks

    def clear_structures(self):
        self.bu_AND_OR = None
        self.td_AND_OR = None
        self.bu_landmarks = None
        self.td_landmarks = None
        gc.collect()

    # UTILITARY
    # def print_landmarks(self, node_id):
    #     print(f'SPECIFIC landmarks of {self.and_or_graph.nodes[node_id]}')
    #     for lm in self.landmarks[node_id]:
    #         print(f'\tlm: {self.and_or_graph.nodes[lm]}')

# if __name__ == '__main__':
#     graph = AndOrGraph(None, debug=True)  # Ensure correct initialization
#     lm = Landmarks(graph)
#     lm.generate_lms()
#     for node_id, lms in enumerate(lm.landmarks):
#         print(f"node{node_id} {lm.nodes[node_id]}")
#         for lm_id in lms:
#             print(f"\tlm {lm.nodes[lm_id]}")
