from collections import deque
from copy import deepcopy
import gc
import math

from Pytrich.ProblemRepresentation.and_or_graph import AndOrGraph
from Pytrich.ProblemRepresentation.and_or_graph import NodeType
from Pytrich.ProblemRepresentation.and_or_graph import ContentType
from Pytrich.model import Model
class Landmarks:
    def __init__(self, model:Model, bu:bool, bid:bool, mt:bool):
        self.model=model
        self.count_operator_lms = 0
        self.count_abtask_lms  = 0
        self.count_fact_lms    = 0
        self.count_method_lms  = 0
        self.count_disjunction_lms = 0

        self.valid_disjunctions = []
        self.gn_fact_orderings = []
        self.gn_task_orderings = []
        self.td_lms    = 0
        self.bid_lms   = 0
        self.bu_lms    = 0
        self.mt_lms    = 0
        self.mt_graph  = None
        self.mt_count  = None
        self.mt_lookup = None
        self.bu_graph  = None
        self.bu_count  = None
        self.bu_lookup = None
        self.td_graph  = None
        self.td_count  = None
        self.td_lookup = None
        if mt:
            self.mt_graph  = AndOrGraph(model, graph_type=2)
            self.mt_count  = len(self.mt_graph.nodes)
            self.mt_lookup = [None] * self.mt_count
        if bu:
            self.bu_graph  = AndOrGraph(model, graph_type=0)
            self.bu_count  = len(self.bu_graph.nodes)
            self.bu_lookup = [None] * self.bu_count
        if bid:
            self.td_graph  = AndOrGraph(model, graph_type=1)
            self.td_count  = len(self.td_graph.nodes)
            self.td_lookup = [None] * self.td_count
    
    def generate_mt_table(self, reinitialize=True):
        self._generate_lm_table(self.mt_lookup, self.mt_graph, reinitialize)
    
    def generate_bu_table(self, state=None, reinitialize=True):
        if not reinitialize:
            self.bu_graph.update_bu_graph(state)
        self._generate_lm_table(self.bu_lookup, self.bu_graph, reinitialize)

    def generate_td_table(self, reinitialize=True):
        self._generate_lm_table(self.td_lookup, self.td_graph, reinitialize)
    
    def _generate_lm_table(self, lm_table, and_or_graph, reinitialize):
        """
        
        We calculate landmarks using binary representation
        """
        queue = deque([node for node in and_or_graph.nodes if node and (len(node.predecessors) == 0 or node.type == NodeType.INIT)])
        it=0

        for node in and_or_graph.nodes:
            if node and node.type == NodeType.INIT:
                lm_table[node.ID] = 0
            if reinitialize:
            #else:
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
        if reinitialize:
            print(f'ITERATIONS {it}')

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

    def top_down_lms(self):
        for lm in range(self.bu_lms.bit_length()):
            if self.bu_lms & (1 << lm):
                self.td_lms |= self.td_lookup[lm]

    def bottom_up_lms(self, state, task_network, reinitialize=True):
        # GOAL SET: tnI U G
        # compute landmarks based on the initial state and goal conditions
        self.bu_lms = state
        if not reinitialize:
            for fact_pos in range(self.model.goals.bit_length()):
                if self.model.goals & (1 << fact_pos) and ~state & (1 << fact_pos):
                #if self.model.goals & (1 << fact_pos): # and ~self.model.initial_state & (1 << fact_pos):
                    self.bu_lms |= self.bu_lookup[fact_pos]
            
                
        # compute landmarks based on task network
        for t in task_network:
            self.bu_lms |= self.bu_lookup[t.global_id]

    def mandatory_tasks_lms(self, task_network):
        # GOAL SET: tnI U G
        # compute landmarks based on the initial state and goal conditions
        self.mt_lms = 0
        # compute landmarks based on task network
        for t in task_network:
            self.mt_lms |= self.mt_lookup[t.global_id]


    def compute_ucp(self, landmarks):
        """
        Compute Uniform Cost Partitioning (UCP) for disjunctive landmarks.
        
        The function does the following:
          1. For each disjunctive landmark in `landmarks`, assign each element a unique index 
             (stored in self.index_of) if not already set.
          2. Record in self.appears_in the list of disjunct indices in which each landmark element appears.
          3. Count the unary landmarks (single-element sets) versus disjunctive ones.
          4. For each unique landmark element (assumed to have cost 1), assign a cost share equal 
             to 1 divided by its number of appearances.
          5. Sets self.lms to a bitmask with one bit per unique landmark element.
        """
        # Initialize or reset data structures.
        if not hasattr(self, "index_of"):
            self.index_of = {}
            for node in self.bu_graph.nodes:
                self.index_of[node.ID] = -1
        if not hasattr(self, "appears_in"):
            self.appears_in = {}
        if not hasattr(self, "ucp_cost"):
            self.ucp_cost = []
        
        # Reset counts.
        self.count_operator_lms = 0
        self.count_method_lms = 0
        self.count_disjunction_lms = 0

        # Induce disjunctions of operators for fact landmarks,
        # and disjunction of methods for abstract tasks.
        # Assign a unique index for each landmark element and record its appearances.
        iof = 0
        dlm=0
        for lm_id in range(landmarks.bit_length()):
            if ~landmarks & (1 << lm_id):
                continue

            node = self.bu_graph.nodes[lm_id]
            if node.type == NodeType.INIT:
                continue
            
            curr_lm = []
            if node.content_type == ContentType.METHOD:
                self.count_method_lms += 1
                curr_lm = [lm_id]
            elif node.content_type == ContentType.OPERATOR:
                self.count_operator_lms += 1
                curr_lm = [lm_id]
            else:
                self.count_disjunction_lms += 1
                curr_lm = [pred.ID for pred in node.predecessors]
            for ulm in curr_lm:
                if self.index_of.get(ulm, -1) == -1:
                    self.index_of[ulm] = iof
                    self.appears_in[iof] = []
                    iof += 1
                self.appears_in[self.index_of[ulm]].append(dlm)
            dlm+=1

        # cost of each disjunction landmark
        #for each unary landmark compute the ucp cost of it
        self.ucp_cost = [math.inf for _ in range(dlm)]
        self.appears_in[-1]=[]
        for uid, appearance_list in self.appears_in.items():
            count = len(appearance_list)
            ucp_ulm = 1.0 / count if count > 0 else 0.0
            # for each disjunction the unary landmark appears,
            # check if its ucp cost
            #   is the lowest cost (thus the cost of the disjunction)
            for lm_index in appearance_list:
                if self.ucp_cost[lm_index] > ucp_ulm:
                    self.ucp_cost[lm_index] = ucp_ulm
        
             
        self.bu_lms = (1 << dlm) - 1
        return self.ucp_cost


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
        self.gn_fact_orderings = [[] for _ in range(len(self.model.facts))]  # NOTE: only considering facts for now
        
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
                        self.gn_fact_orderings[ord[1]].append(ord[0])
                
        # print the greedy necessary orderings with fact names
        # for f_prime, f_lst in enumerate(self.lm_gn_orderings):
        #     if not f_lst:
        #         continue
        #     f_prime_name = self.model.get_component(f_prime).name
        #     formatted_orderings = [
        #         f"{self.model.get_component(f_id).name} < {f_prime_name}" for f_id in f_lst
        #     ]
        #     print(f"Orderings for {f_prime_name}: \n\t" + '\n\t'.join(formatted_orderings))

    def compute_gn_task_orderings(self, lm_table, and_or_graph, lm_set):
        self.gn_task_orderings = [[] for _ in range(len(self.model.abstract_tasks)+len(self.model.operators))]  # For tasks instead of facts
        for t_prime_id, node_t_prime in enumerate(and_or_graph.nodes):
            if  (node_t_prime.content_type == ContentType.OPERATOR or node_t_prime.content_type == ContentType.ABSTRACT_TASK) and lm_set & (1 << t_prime_id):
                first_achievers = None
                achievers = None
                
                if node_t_prime.content_type == ContentType.OPERATOR:
                    node_t_prime = and_or_graph.nodes[and_or_graph.components_count+node_t_prime.LOCALID]
                first_achievers = [
                    pred_node for pred_node in node_t_prime.predecessors
                    if not (lm_table[pred_node.ID] & (1 << t_prime_id))
                ]
                achievers = [
                    pred_node for pred_node in node_t_prime.predecessors
                ]
                if not first_achievers:
                    continue
                
                
                # Compute the intersection of task compound tasks
                tmp_t_pred = [
                    {pred_node.ID for pred_node in fa.predecessors
                    if pred_node.content_type in {ContentType.ABSTRACT_TASK}}
                    for fa in first_achievers
                ]
                
                t_union = set.union(*tmp_t_pred) if tmp_t_pred else set()
                t_intersection = set.intersection(*tmp_t_pred) if tmp_t_pred else set()
                
                # if len(first_achievers) < sum([len(self.model.get_component(tID).decompositions) for tID in t_union]) :
                #     print(node_t_prime)
                #     print(f'\tachievers: {len(achievers)} first achivers: {len(first_achievers)}')
                #     print(f'\ttotal choices: {sum([len(self.model.get_component(tID).decompositions) for tID in t_union])}')
                #     print(f'\ttotal required again: {len(t_union)}')
                
                # Any task common to all first achievers is a predecessor of t'
                go = [
                    (t_id, t_prime_id) for t_id in t_intersection
                ]
                if go:
                    for ord in go:
                        self.gn_task_orderings[ord[0]-len(self.model.facts)].append(ord[1])

        # Print the greedy necessary orderings with task names
        # for t_prime, t_lst in enumerate(self.gn_task_orderings):
        #     if not t_lst:
        #         continue
        #     t_prime +=len(self.model.facts)
        #     t_prime_name = self.model.get_component(t_prime).name
        #     formatted_orderings = [
        #         f"{self.model.get_component(t_id).name}({self.model.get_component(t_id).global_id}) < {t_prime_name}" for t_id in t_lst
        #     ]
        #     print(f"Orderings for {t_prime_name}: \n\t" + '\n\t'.join(formatted_orderings))

         
    def identify_lms(self, lm_set, and_or_graph):
        for lm_id in range(lm_set.bit_length()):
            if lm_id < len(and_or_graph.nodes) and lm_set & (1 << lm_id):
                if and_or_graph.nodes[lm_id].content_type == ContentType.FACT:
                    self.count_fact_lms +=1
                elif and_or_graph.nodes[lm_id].content_type == ContentType.METHOD:
                    self.count_method_lms +=1
                elif and_or_graph.nodes[lm_id].content_type == ContentType.ABSTRACT_TASK:
                    self.count_abtask_lms +=1
                elif and_or_graph.nodes[lm_id].content_type == ContentType.OPERATOR:
                    self.count_operator_lms +=1

    def clear_structures(self):
        self.bu_graph = None
        self.r_graph = None
        self.bu_lookup = None
        self.r_lookup = None
        gc.collect()