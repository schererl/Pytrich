from collections import deque
from copy import deepcopy
import gc

from Pytrich.ProblemRepresentation.and_or_graph import AndOrGraph
from Pytrich.ProblemRepresentation.and_or_graph import NodeType
from Pytrich.ProblemRepresentation.and_or_graph import ContentType
from Pytrich.model import Model

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
    def initialize_lms(self, lms):
        # for lm_id in new_lms:
        #     if ~self.lms & (1 << lm_id):
        #         self.lms |= (1 << lm_id)
        #         self.number_lms+=1
        self.lms = lms
        self.number_lms = lms.bit_count()
    
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
    def __init__(self, model:Model, bidirectional=False):
        self.model=model
        self.bidirectional=bidirectional
        self.bu_graph  = AndOrGraph(model, graph_type=0) # bottom-up and or graph
        self.bu_count  = len(self.bu_graph.nodes)
        self.bu_lookup = [None] * self.bu_count # bottom-up look-up table
        #self.bu_lms    = set()
        self.bu_lms    = 0
        if bidirectional:
            self.td_graph  = AndOrGraph(model, graph_type=1)  # top-down and or graph
            self.td_count  = len(self.td_graph.nodes)
            self.td_lookup = [None] * self.td_count # top-down look-up table
            #self.td_lms    = set()
            self.td_lms    = 0
            #self.bid_lms   = set()
            self.bid_lms   = 0
            
        self.count_task_lms = 0
        self.count_fact_lms = 0
        self.count_method_lms = 0
        # self.task_lms = set()
        # self.fact_lms = set()
        # self.method_lms = set()
        self.valid_disjunctions = []
        self.lm_gn_orderings = []

    def generate_bottom_up(self):
        self._generate_lms(self.bu_lookup, self.bu_graph)
    def generate_top_down(self):
        self._generate_lms(self.td_lookup, self.td_graph)
    
    # def _generate_lms(self, lm_table, and_or_graph):
    #     """
    #     Original landmark extraction:
    #       We refer to it as 'bottom-up landmarks' because it captures the HTN hierarchy this way
    #       see: Höller, D., & Bercher, P. (2021). Landmark Generation in HTN Planning. Proceedings of the AAAI Conference on Artificial Intelligence
    #     """
    #     queue = deque([node for node in and_or_graph.nodes if node and (len(node.predecessors) == 0 or node.type == NodeType.INIT)])
    #     it = 0
    #     while queue:
    #         node = queue.popleft()
    #         it+=1
            
    #         new_landmarks= None
    #         pred_lms = []
    #         all_lms= False
    #         for pred in node.predecessors:
    #             lms = lm_table[pred.ID]
    #             if lms is None:
    #                 all_lms=True
    #                 continue
    #             pred_lms.append(lm_table[pred.ID])
            
    #         if node.type == NodeType.OR and node.predecessors:
    #             # in case of some predecessor had all landmarks, just ignore it and apply the interesection of the others
    #             if len(pred_lms) >= 1:
    #                 new_landmarks = set.intersection(*(pred_lms)) | {node.ID}
                
    #         elif node.type == NodeType.AND and node.predecessors:
    #             # if some predecessor had all landmarks, consider node containing all landmarks also
    #             if not all_lms:
    #                 new_landmarks = set.union(*(pred_lms)) | {node.ID}
    #         else:
    #             new_landmarks = {node.ID}
            
    #         if  new_landmarks != lm_table[node.ID]:
    #             lm_table[node.ID] = new_landmarks
    #             for succ in node.successors:
    #                 queue.append(succ)
    #     print(f'iterations {it}')

    def _generate_lms(self, lm_table, and_or_graph):
        """
        
        We calculate landmarks using binary representation
        """
        queue = deque([node for node in and_or_graph.nodes if node and (len(node.predecessors) == 0 or node.type == NodeType.INIT)])
        it=0
        for node in and_or_graph.nodes:
            if node and node.type == NodeType.INIT:
                lm_table[node.ID] = 0
            else:
                lm_table[node.ID] = (1 << len(and_or_graph.nodes)) - 1
        while queue:
            it+=1
            node = queue.popleft()
            new_landmarks= 0
            if node.type == NodeType.OR and node.predecessors:
                new_landmarks= (1 << len(and_or_graph.nodes)) - 1 # initialize intersection operation with ALLNODES
                for pred_lm in node.predecessors:
                    new_landmarks &= lm_table[pred_lm.ID]
            elif node.type == NodeType.AND and node.predecessors:
                for pred_lm in node.predecessors:
                    new_landmarks |= lm_table[pred_lm.ID]
            new_landmarks |= (1<<node.ID)
            
            if  new_landmarks != lm_table[node.ID]:
                lm_table[node.ID] = new_landmarks
                for succ in node.successors:
                    queue.append(succ)
        print(f'ITERATIONS {it}')
    
    # def bidirectional_lms(self):
    #     visited = set()
    #     queue   = deque()  
    #     queue.extend(list(self.td_lms))
        
    #     # iterate over each landmark and increment with td and bu landmarks while new landarks are discovered
    #     while queue:
    #         node_id = queue.popleft()
    #         visited.add(node_id)
    #         # top-down landmarks
    #         for lm_id in self.td_lookup[node_id]:
    #            if not lm_id in visited:
    #                queue.append(lm_id)
            
    #         if node_id >= self.bu_graph.components_count: # skip recomposition nodes, they dont exist in bottom-up graph
    #             continue
    #         # bottom-up landmarks
    #         for lm_id in self.bu_lookup[node_id]:
    #             if not lm_id in visited:
    #                 queue.append(lm_id)

    #         self.bid_lms.add(node_id)

    #     for lm_id in self.bid_lms:
    #         if self.bu_graph.nodes[lm_id].content_type == ContentType.FACT:
    #             self.fact_lms.add(lm_id)
    #         elif self.bu_graph.nodes[lm_id].content_type == ContentType.METHOD:
    #             self.method_lms.add(lm_id)
    #         else:
    #             self.task_lms.add(lm_id)


    def bidirectional_lms(self):
        self.bid_lms = 0
        new_lms = self.bu_lms
        it_n = 0
        # iterate over each landmark and increment with td and bu landmarks while new landmarks are discovered
        while new_lms != self.bid_lms:
            it_n += 1
            self.bid_lms = new_lms
            for n_id in range(len(self.bu_graph.nodes)):
                if new_lms & (1 << n_id):
                    new_lms |= self.bu_lookup[n_id]
                if new_lms & (1 << n_id):
                    new_lms |= self.td_lookup[n_id]
        self.bid_lms = self.bid_lms & ((1 << len(self.bu_graph.nodes))-1) #remove recomposition nodes
        
        

    # def bidirectional_lms(self):
    #     print(f'HERE')
    #     visited = 0
    #     queue   = deque()
    #     for bit in range(self.bu_lms.bit_length()):
    #         if self.bu_lms & (1 << bit):
    #             queue.append(bit)
        
    #     # iterate over each landmark and increment with td and bu landmarks while new landmarks are discovered
    #     while queue:
    #         node_id = queue.popleft()
    #         if visited & (1 << node_id):
    #             continue
            
    #         visited |= 1 << node_id
    #         # top-down landmarks
    #         print(self.td_lookup[node_id].bit_length())
    #         for lm_id in range(self.td_lookup[node_id].bit_length()):
    #             if self.td_lookup[node_id] & (1 << lm_id) and not visited & (1 << lm_id):
    #                 queue.append(lm_id)
            
    #         if node_id >= self.bu_graph.components_count: # check if is a recomposition node
    #             continue
            
    #         # bottom-up landmarks
    #         for lm_id in range(self.bu_lookup[node_id].bit_length()):
    #             if self.bu_lookup[node_id] & (1 << lm_id) and not visited & (lm_id << 1):
    #                 queue.append(lm_id)

    #         self.bid_lms |= (1 << node_id)

    #     print(f'ENDED')
        
        
    
    def top_down_lms(self):
        for lm in range(self.bu_lms.bit_length()):
            if self.bu_lms & (1 << lm):
                self.td_lms |= self.td_lookup[lm]

    def bottom_up_lms(self):
        # GOAL SET: tnI U G
        # compute landmarks based on the initial state and goal conditions
        self.bu_lms = self.model.initial_state
        for fact_pos in range(self.model.goals.bit_length()):
            if self.model.goals & (1 << fact_pos) and ~self.model.initial_state & (1 << fact_pos):
            #if self.model.goals & (1 << fact_pos): # and ~self.model.initial_state & (1 << fact_pos):
                self.bu_lms |= self.bu_lookup[fact_pos]
            
                
        # compute landmarks based on task network
        for t in self.model.initial_tn:
            self.bu_lms |= self.bu_lookup[t.global_id]
                
    def compute_gn_fact_orderings(self, lm_table, and_or_graph, lm_set):
        '''
        Compute greedy necessary orderings among facts.
        1) For each fact' (fact prime) landmark
        2) Get the actions predecessors (first-achievers) of this fact'
        3) Include a precedence fact < fact', for each fact which is a precondition of every first-achiever of fact prime

        OBS: 
            If a fact f is a precondition of every achiever of f',
            f must be true right before f', since all possible ways on achieving f' need f being true.
            Whenever fact f is made true and then deleted without reaching f', f needs to be reached again.
            This is called GREEDY NECESSARY ORDERING
        '''
        self.lm_gn_orderings = [[] for _ in range(len(self.model.facts))]  # NOTE: only considering facts for now
        
        for f_prime_id, node_f_prime in enumerate(and_or_graph.nodes):
            if (lm_set & (1 << f_prime_id)) and node_f_prime.content_type == ContentType.FACT:
                # compute first achievers FA(f'): actions a in pred(f') where f' not in LM(a)
                first_achievers = [
                    pred_node for pred_node in node_f_prime.predecessors
                    if not (lm_table[pred_node.ID] & (1 << f_prime_id))
                ]
                if not first_achievers:
                    continue

                # compute the intersection of fact predecessors of first-achievers
                tmp_f_pred = [
                    {pred_node.ID for pred_node in fa.predecessors if pred_node.content_type == ContentType.FACT and node_f_prime.type != NodeType.INIT}
                    for fa in first_achievers
                ]
                
                f_intersection = set.intersection(*tmp_f_pred)
                # any fact that is common to all first achievers is a predecessor of f'
                go = [
                    (f_id, f_prime_id) for f_id in f_intersection
                ]
                if go:
                    for ord in go:
                        self.lm_gn_orderings[ord[1]].append(ord[0])
                
        # print the greedy necessary orderings with fact names
        for f_prime, f_lst in enumerate(self.lm_gn_orderings):
            if not f_lst:
                continue
            f_prime_name = self.model.get_component(f_prime).name
            formatted_orderings = [
                f"{self.model.get_component(f_id).name} < {f_prime_name}" for f_id in f_lst
            ]
            print(f"Orderings for {f_prime_name}: \n\t" + '\n\t'.join(formatted_orderings))

    def compute_gn_task_orderings(self, lm_table, and_or_graph, lm_set):
        self.lm_gn_orderings = [[] for _ in range(len(self.model.abstract_tasks)+len(self.model.operators))]  # For tasks instead of facts

        for t_prime_id, node_t_prime in enumerate(and_or_graph.nodes):
            
            if lm_set & (1 << t_prime_id):
                first_achievers = None
                if node_t_prime.content_type == ContentType.ABSTRACT_TASK:
                    first_achievers = [
                        pred_node for pred_node in node_t_prime.predecessors
                        if not (lm_table[pred_node.ID] & (1 << t_prime_id))
                    ]
                elif node_t_prime.content_type == ContentType.OPERATOR:
                    r_node = and_or_graph.nodes[and_or_graph.components_count+node_t_prime.LOCALID]
                    first_achievers = [
                        pred_node for pred_node in r_node.predecessors
                        if not (lm_table[pred_node.ID] & (1 << t_prime_id))
                    ]
                if not first_achievers:
                    continue
                print(node_t_prime)
                print(f'\t{[self.model.get_component(pred.ID).name for pred in first_achievers]}')
                # Compute the intersection of task compound tasks
                tmp_t_pred = [
                    {pred_node.ID for pred_node in fa.predecessors
                    if pred_node.content_type in {ContentType.ABSTRACT_TASK}}
                    for fa in first_achievers
                ]

                t_intersection = set.intersection(*tmp_t_pred) if tmp_t_pred else set()
                print(f'\t\t{[self.model.get_component(tID).name for tID in t_intersection]}')
                # Any task common to all first achievers is a predecessor of t'
                go = [
                    (t_id, t_prime_id) for t_id in t_intersection
                ]
                if go:
                    for ord in go:
                        self.lm_gn_orderings[ord[1]-len(self.model.facts)].append(ord[0])

        # Print the greedy necessary orderings with task names
        for t_prime, t_lst in enumerate(self.lm_gn_orderings):
            if not t_lst:
                continue
            t_prime +=len(self.model.facts)
            t_prime_name = self.model.get_component(t_prime).name
            formatted_orderings = [
                f"{self.model.get_component(t_id).name} < {t_prime_name}" for t_id in t_lst
            ]
            print(f"Orderings for {t_prime_name}: \n\t" + '\n\t'.join(formatted_orderings))

         
    def identify_lms(self, lm_set):
        for lm_id in range(lm_set.bit_length()):
            if lm_id < len(self.bu_graph.nodes) and lm_set & (1 << lm_id):
                if self.bu_graph.nodes[lm_id].content_type == ContentType.FACT:
                    self.count_fact_lms +=1
                elif self.bu_graph.nodes[lm_id].content_type == ContentType.METHOD:
                    self.count_method_lms +=1
                elif self.bu_graph.nodes[lm_id].content_type == ContentType.ABSTRACT_TASK or self.bu_graph.nodes[lm_id].content_type == ContentType.OPERATOR:
                    self.count_task_lms +=1
                    
        # for lm_id in lm_set:
        #     node = self.bu_graph.nodes[lm_id]
        #     if node.content_type == ContentType.FACT:
        #         self.fact_lms.add(lm_id)
        #     elif node.content_type == ContentType.METHOD:
        #         self.method_lms.add(lm_id)
        #     elif node.content_type == ContentType.ABSTRACT_TASK or node.content_type == ContentType.OPERATOR:
        #         self.task_lms.add(lm_id)

    # TODO: refactor minimal disjunctions
    def _compute_minimal_fact_disjunction(self, disj_operators, disj_precons, TA):
        """
        This function finds a minimal set of fact preconditions that covers all operators in the disjunction.
        """
        return None
        # minimal_facts = set()
        # all_facts = set.union(*disj_precons)
        
        # fact_coverage = {fact: set() for fact in all_facts}
        # for op_disj_i, op in enumerate(disj_operators):
        #     for fact in disj_precons[op_disj_i]:
        #         fact_coverage[fact].add(op)
        # # keep track of covered operators
        # covered_operators = set()
        # # greedy approach: select facts that cover the most uncovered operators
        # while len(covered_operators) < TA and fact_coverage:
        #     # find the fact that covers the most uncovered operators
        #     best_fact = max(fact_coverage, key=lambda f: len(fact_coverage[f] - covered_operators))
        #     best_coverage = fact_coverage[best_fact] - covered_operators
        #     # add this fact to the minimal set
        #     minimal_facts.add(best_fact)
        #     # mark these operators as covered
        #     covered_operators.update(best_coverage)
        #     # remove the best fact from future consideration
        #     del fact_coverage[best_fact]
        
        # # if it is not possible cover all return set()
        # if len(covered_operators) < TA:
        #     return set()

        # # remove facts used into minimal facts from each disjunction 
        # for i, precon_set in enumerate(disj_precons):
        #     disj_precons[i] = precon_set - minimal_facts
        # return minimal_facts
    # TODO: refactor minimal disjunctions
    def _compute_minimal_disjunctions(self):
        pass
        # for lm_fact in self.bu_lms:
        #     o_achievers = set()
        #     for o_a in self.model.operators:
        #         if  o_a.add_effects_bitwise & (1 << lm_fact) != 0:
        #             o_achievers.add(o_a)
        #     # OPTION 1: fact preconditions for operator disjunction
        #     disjunctive_preconitions = [set(o_a.get_precons_bitfact()) for o_a in o_achievers]
        #     # Get the intersection of disjunctive landmarks
        #     if disjunctive_preconitions:
        #         interesection_lms = set.intersection(*disjunctive_preconitions)
        #         if not interesection_lms:
                    
        #             # compute maximal minimal disjunctions
        #             total_achievers = len(o_achievers)
        #             while disjunctive_preconitions:
        #                 minimal_disj = self._compute_minimal_fact_disjunction(o_achievers, disjunctive_preconitions, total_achievers)
        #                 if not minimal_disj or len(minimal_disj) > 4:
        #                     break
        #                 if  minimal_disj not in self.valid_disjunctions:
        #                     self.valid_disjunctions.append(minimal_disj)

    def clear_structures(self):
        self.bu_graph = None
        self.r_graph = None
        self.bu_lookup = None
        self.r_lookup = None
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
