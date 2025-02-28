from collections import deque
from copy import deepcopy
import heapq
import math
import time
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
        
    def hmax_update(self, cut, cut_cost, pcf, cost):
        needs_update = set()
        for c in cut:
            # old_cost = cost[c]
            cost[c] -= cut_cost
            node_c = self.graph.nodes[c]
            #print(f"Cut update: Node {node_c.str_name} (ID {c}) cost updated from {old_cost} to {cost[c]} (subtracted cut_cost {cut_cost})")
            for succ in node_c.successors:
                needs_update.add(succ.ID)
            #    print(f"  Adding successor {succ.str_name} (ID {succ.ID}) for update")
        
        while needs_update:
            next_updates =set()
            #print("\n--- New update round ---")
            #update_names = [self.graph.nodes[nid].str_name for nid in needs_update]
            #print("Nodes to update:", len(update_names))

            for nid in needs_update:
                node = self.graph.nodes[nid]
                if node.type == NodeType.AND:
                    max_val=-math.inf
                    curr_pcf = -1
                    for pred in node.predecessors:
                        if cost[pred.ID] > max_val:
                            max_val=cost[pred.ID]
                            curr_pcf=pred.ID
                    # print(f"AND Node {node.str_name} (ID {nid}):")
                    # print(f"  - Max predecessor cost = {max_val} from node {self.graph.nodes[curr_pcf].str_name if curr_pcf is not None else 'None'}")
                    # print(f"  - Local cost = {self.local_costs.get(nid, 0)}")
                    # print(f"  - Current cost = {cost[nid]}, New computed cost = {max_val + self.local_costs[nid]}")
                    if pcf[nid] != curr_pcf or max_val != cost[nid]:
                        pcf[nid] = curr_pcf
                        nid_old_cost = cost[nid]
                        cost[nid] = max_val + self.local_costs[nid]
                        for succ in node.successors:
                            # [OPT] only update successor (OR nodes) if the new value affects the successors
                            if pcf[succ.ID] and \
                                ((pcf[succ.ID] != nid and cost[pcf[succ.ID]] > cost[nid]) or \
                                (pcf[succ.ID] == nid and nid_old_cost != cost[nid])):
                                next_updates.add(succ.ID)
                elif node.type == NodeType.OR:
                    min_val=math.inf
                    curr_pcf = -1 # pcf for OR nodes is useless, debug verificaiton only
                    # print(f"OR Node {node.str_name} (ID {nid}):")
                    # print(f'Predecessors:')
                    for pred in node.predecessors:
                        #print(f'\t{pred.str_name} and cost {cost[pred.ID]}')
                        if cost[pred.ID] < min_val:
                            min_val=cost[pred.ID]
                            curr_pcf=pred.ID
                    # print()
                    # print(f"  - Min predecessor cost = {min_val} from node {self.graph.nodes[curr_pcf].str_name if curr_pcf is not None else 'None'}")
                    # print(f"  - Current cost = {cost[nid]}, New computed cost = {min_val}")
                    if min_val != cost[nid]:
                        pcf[nid] = curr_pcf
                        cost[nid] = min_val
                        for succ in node.successors:
                            # [OPT] only update successor (AND nodes) if the new value affects the successors
                            if pcf[succ.ID] == nid:
                                next_updates.add(succ.ID)

            needs_update = next_updates



    def compute_h_max(self):
        cost = {}
        num_ft = {}
        forced_true = {}
        heap = []
        for node in self.graph.nodes:
            num_ft[node.ID]=0
            forced_true[node.ID]= False
            if node.type == NodeType.INIT:
                cost[node.ID] = 0
                heapq.heappush(heap, (0, node.ID))
            elif node.type == NodeType.AND:
                cost[node.ID] = -math.inf
            else:
                cost[node.ID] = math.inf
        pcf = {node.ID: None for node in self.graph.nodes}
        while heap:
            c, u_id = heapq.heappop(heap)
            u_node = self.graph.nodes[u_id]
            # print(f'{u_node.str_name}')
            # print(f'\t{u_node.type}')
            # print(f'\t{num_ft[u_id]} {len(u_node.predecessors)}')
            # print(f'\t{c} {cost[u_id]}')
            # assert (u_node.type == NodeType.AND and num_ft[u_id] == len(u_node.predecessors)) or\
            #     (u_node.type == NodeType.OR and num_ft[u_id] >= 1) or\
            #     (u_node.type == NodeType.INIT)
            
            if cost[u_id] != c:
                continue
            if forced_true[u_id]:
                continue
            forced_true[u_id]=True
            for v_node in u_node.successors:
                v_id = v_node.ID
                num_ft[v_id]+=1
                if v_node.type == NodeType.OR:
                    new_cost = c
                    if new_cost < cost[v_id]:
                        cost[v_id]=c
                        pcf[v_id] = u_id
                        heapq.heappush(heap, (c, v_id))
                        # print(f'\tnew cost: {cost[v_id]} to {v_node.str_name}')
                elif v_node.type == NodeType.AND and num_ft[v_id] == len(v_node.predecessors):
                    high_predv = -1
                    pcf_v  = -1
                    lc_v = self.local_costs[v_id]
                    for pred in v_node.predecessors:
                        #assert cost[pred.ID] < math.inf
                        #assert forced_true[pred.ID]
                        if high_predv < cost[pred.ID]:
                            high_predv = cost[pred.ID]
                            pcf_v = pred.ID
                    v_cost = high_predv + lc_v
                    cost[v_id]= v_cost
                    pcf[v_id] = pcf_v
                    # print(f'\tnew cost: {cost[v_id]} to {v_node.str_name} ')
                    heapq.heappush(heap, (v_cost, v_id))

        # for node in self.graph.nodes:
        #     print(f'{node.ID}\ttype: {node.type}\tcost: {cost[node.ID]}\tpcf: {str(pcf[node.ID])}\t pcf-cost: {str(cost[pcf[node.ID]]) if node.type==NodeType.AND else '---'}')
        # for t in self.model.initial_tn:
        #     node = self.graph.nodes[t.global_id]
        #     pcf_node = self.graph.nodes[pcf[node.ID]]
        #     print(f'{t.name}\ttype: GOAL_NODE\tcost: {cost[node.ID]}\tpcf: {pcf_node.str_name}\t pcf-cost: {str(cost[pcf[node.ID]]) if node.type==NodeType.AND else '---'}')
        #     pcf_of_pcf = self.graph.nodes[pcf[pcf_node.ID]]
        #     print(f'{pcf_of_pcf.str_name}\tcost: {cost[pcf_of_pcf.ID]}')
        # exit(0)            
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
        start_time = time.perf_counter()
        h = 0
        landmarks = []
        iterations = 0
        cost, pcf = self.compute_h_max()
        while True:
            iterations+=1
            #cost, pcf = self.compute_h_max()
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
            self.hmax_update(cut, cut_cost, pcf, cost)
            
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
        elapsed_time = time.perf_counter() - start_time
        print(f"compute_lm_cut completed in {elapsed_time:.6f} seconds")
        #return h, landmarks
        
    
    def compute_lms(self):
        goals = [task.global_id for task in self.model.initial_tn]
        self.compute_lm_cut(goals)
        
