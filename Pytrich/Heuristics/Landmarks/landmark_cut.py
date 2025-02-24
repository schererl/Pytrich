from collections import deque
from copy import deepcopy
import heapq
import math
from Pytrich.ProblemRepresentation.and_or_graph import AndOrGraph, NodeType, ContentType

class LMCutRC:
    """
    Computes an LM‐Cut heuristic over the Relaxed Composition (RC) graph.
    
    The RC graph is assumed to be an instance of AndOrGraph built via rc_initialize.
    
    Cost propagation:
      - INIT nodes (facts in the initial state) have cost 0.
      - For AND nodes, cost = local_cost (if any) + max_{p in predecessors} cost(p)
      - For OR nodes, cost = min_{p in predecessors} cost(p)
    
    Only operator nodes (i.e. AND nodes with content_type OPERATOR) carry a weight
    (stored in node.weight). These are the only nodes whose cost is reduced when a
    landmark cut is extracted.
    """

    def __init__(self, model):
        self.model= model
        self.graph = AndOrGraph(model, graph_type=3)
        self.lms = set()
        
        self.index_of = {}
        self.appears_in = {}
        self.appears_in[-1]=[]
        self.local_costs = {}
        for node in self.graph.nodes:
            self.index_of[node.ID] = -1
            
            if node is not None and node.type == NodeType.AND:
                self.local_costs[node.ID] = node.weight
                
        print(f'LMCUT LANDMARKS')
        

    def compute_h_max(self):
        """
        Compute hmax values over the RC graph using a Dijkstra-like algorithm.
        :param goal_ids: iterable of node IDs corresponding to goals.
        :return: Tuple (cost, pcf_justif)
          - cost: dict mapping node ID -> computed hmax cost.
          - pcf_justif: dict mapping node ID -> a predecessor AND node ID that led to its current cost.
                    (Precondition choice function to induce the justification graph.)
        """
        cost = {node.ID: math.inf for node in self.graph.nodes if node is not None}
        
        # pcf[n] = -1 and cost[-1]=math.inf for every initialized node n
        # the first time a true node n' reaches n, pcf[n] = n'. because cost[n']
        cost[-1] = math.inf
        pcf = {node.ID: -1 for node in self.graph.nodes if node is not None}
        

        heap = []
        for node in self.graph.nodes:
            if node.type == NodeType.INIT:
                cost[node.ID] = 0
                heapq.heappush(heap, (0, node.ID))
               
        while heap:
            d, u_id = heapq.heappop(heap)
            #print(f'{self.graph.nodes[u_id].str_name}:{d}')
            if d > cost[u_id]:
                continue  # stale entry
            u_node = self.graph.nodes[u_id]
            # relax nodes
            for v_node in u_node.successors:
                if v_node.type == NodeType.AND:
                    # AND nodes: candidate = local_cost(v) + max_{p in pred(v)} cost(p)
                    local = self.local_costs[v_node.ID]
                    pred_costs = [cost[p.ID] for p in v_node.predecessors]
                    max_val = max(pred_costs) if pred_costs else 0
                    candidate = local + max_val
                    
                    # update pcf of AND node v: pcf[v] = u if the cost of v is higher than current pcf of v.
                    pcf_nodeid = None
                    curr_pcf = pcf[v_node.ID]
                    if cost[u_id] > cost[curr_pcf] or \
                        cost[curr_pcf] == math.inf:
                        pcf_nodeid = u_id

                elif v_node.type == NodeType.OR:
                    # OR nodes: candidate = min_{p in pred(v)} cost(p)
                    pred_costs = [cost[p.ID] for p in v_node.predecessors]
                    candidate = min(pred_costs) if pred_costs else math.inf
                    pcf_nodeid = -1
                else: # in case of reaching an INIT node
                    continue

                if candidate < cost[v_node.ID]:
                    cost[v_node.ID] = candidate
                    pcf[v_node.ID] = pcf_nodeid
                    #print(f'\t{self.graph.nodes[v_node.ID].str_name} {candidate}')
                    heapq.heappush(heap, (candidate, v_node.ID))
        return cost, pcf

    def find_landmark_cut(self, cost, pcf, goals, hmax_value):
        """
        Extract a landmark cut from the RC graph.
        
        1) Starting at a goal node that has cost equal to hmax_value,
            follow backward to produce the cut. 
        2) OR nodes includes EVERY AND node predecessor into the stack.
        3) AND nodes includes ONE predecessor into the stack 
            that justify AND's cost (precondition choice function)
        - When an AND node has cost different than its pcf, 
            this means the AND node is part of the cut.
        """
        cut = set()
        stack = []
        visited = set()
        
        for gid in goals:
            if cost[gid] == hmax_value:
                stack.append(gid)
                break
                
        while stack:
            v_id = stack.pop()
            if v_id in visited:
                continue
            visited.add(v_id)
            v_node = self.graph.nodes[v_id]
            
            # OR node, include all predecessors with the same cost of v
            if v_node.type == NodeType.OR:
                for u_node in v_node.predecessors:
                    #if cost[u_node.ID] == cost[v_id]:
                    stack.append(u_node.ID)
            else: 
            # AND node: get pcf node check pcf -> v
                u_id = pcf[v_id]
                if cost[u_id] == math.inf: # unsatisfiable test: pcf max value is inf
                    return
                elif cost[u_id] < cost[v_id]: # cut test: pcf has a lower cost of v
                    cut.add(v_id)
                else: # goal zone: pcf has the same cost as v, both are in the goal zone
                    stack.append(u_id)
        
        return cut

    
    def compute_lm_cut(self, goal_ids):
        """
        Compute the LM-Cut heuristic over the Relaxed Composition Graph 
        for the given goal nodes.
        """
        h = 0
        landmarks = []
        iterations = 0
        while True:
            iterations+=1
            cost, pcf = self.compute_h_max()
            hmax_val = max(cost.get(gid, math.inf) for gid in goal_ids)
            #print(f'iteration {iterations} {hmax_val}')
            if hmax_val == 0:
                break
            if hmax_val == math.inf:
                return math.inf, landmarks

            cut = self.find_landmark_cut(cost, pcf, goal_ids, hmax_val)
            if not cut:
                break

            cut_cost = min(self.local_costs[nid] for nid in cut)
            #print(f'[',end='')
            for nid in cut:
                self.local_costs[nid] -= cut_cost
                #print(f'{self.graph.nodes[nid].str_name} ',end='')
            #print(f']')
            h += cut_cost
            landmarks.append(cut)
            
        # process data structure for tracking lms
        # for each landmark create an index 
        #   and maps the component to the the list of landmark it appears
        #self.lms = landmarks
        self.lms = (1 << len(landmarks)) - 1
        iof = 0
        for i_dlm, dlm in enumerate(landmarks):
            for ulm in dlm:
                if self.index_of[ulm]==-1:
                    self.index_of[ulm]=iof
                    if iof not in self.appears_in:
                        self.appears_in[iof]=[]
                    iof+=1
                self.appears_in[self.index_of[ulm]].append(i_dlm)
                
        # print(landmarks)
        # print(bin(self.lms))
        # print(self.appears_in)
        # for lm in landmarks:
        #     print(f'{[self.graph.nodes[id].str_name + " " + str(self.index_of[id]) for id in lm]}')
        
        #return h, landmarks
        
    
    def compute_lms(self):
        goals = [task.global_id for task in self.model.initial_tn]
        self.compute_lm_cut(goals)
        
