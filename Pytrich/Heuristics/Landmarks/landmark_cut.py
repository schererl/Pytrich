from collections import deque
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

        self.local_costs = {}
        for node in self.graph.nodes:
            if node is not None and node.type == NodeType.AND:
                self.local_costs[node.ID] = node.weight
        print(f'LMCUT LANDMARKS')
        

    def compute_h_max(self, goal_ids):
        """
        Compute hmax values over the RC graph using a Dijkstra-like algorithm.
        
        :param goal_ids: Iterable of node IDs corresponding to goal facts.
        :return: Tuple (cost, support)
          - cost: dict mapping node ID -> computed hₘₐₓ cost.
          - support: dict mapping node ID -> a predecessor node ID that led to its current cost.
                     (Used later for backtracking the landmark cut.)
        """
        # Initialize cost for every node to infinity.
        cost = {node.ID: math.inf for node in self.graph.nodes if node is not None}
        support = {}  # node ID -> predecessor node ID

        # For nodes marked as INIT, set cost = 0.
        for node in self.graph.nodes:
            if node is None:
                continue
            if node.type == NodeType.INIT:
                cost[node.ID] = 0

        # Use a heap (priority queue) initialized with all INIT nodes.
        heap = []
        for node in self.graph.nodes:
            if node is not None and node.type == NodeType.INIT:
                heapq.heappush(heap, (0, node.ID))
                
        while heap:
            d, u_id = heapq.heappop(heap)
            if d > cost[u_id]:
                continue  # stale entry
            u_node = self.graph.nodes[u_id]
            # Relax all successors of u_node.
            for v_node in u_node.successors:
                # Compute candidate cost for v_node based on its type.
                if v_node.type == NodeType.AND:
                    # For AND nodes: candidate = local_cost(v) + max_{p in pred(v)} cost(p)
                    local = self.local_costs.get(v_node.ID, 0)
                    pred_costs = [cost[p.ID] for p in v_node.predecessors]
                    max_val = max(pred_costs) if pred_costs else 0
                    candidate = local + max_val
                    # Determine the predecessor that gives the maximum cost.
                    best_pred = None
                    best_val = -1
                    for p in v_node.predecessors:
                        if cost[p.ID] > best_val:
                            best_val = cost[p.ID]
                            best_pred = p.ID
                elif v_node.type == NodeType.OR:
                    # For OR nodes: candidate = min_{p in pred(v)} cost(p)
                    pred_costs = [cost[p.ID] for p in v_node.predecessors]
                    candidate = min(pred_costs) if pred_costs else math.inf
                    best_pred = None
                    best_val = math.inf
                    for p in v_node.predecessors:
                        if cost[p.ID] < best_val:
                            best_val = cost[p.ID]
                            best_pred = p.ID
                else:
                    continue

                if candidate < cost[v_node.ID]:
                    cost[v_node.ID] = candidate
                    support[v_node.ID] = best_pred
                    heapq.heappush(heap, (candidate, v_node.ID))
        # For debugging:
        # print("Computed h_max costs:", cost)
        return cost, support

    def find_landmark_cut(self, cost, support, goal_ids, hmax_value):
        """
        Extract a landmark cut from the RC graph.
        
        Starting at each goal node (from goal_ids) that has cost equal to hmax_value,
        follow the support pointers backward. When an operator node (AND node with content_type OPERATOR)
        with a positive remaining local cost is encountered, add it to the cut and stop expanding that branch.
        
        :param cost: dict of hₘₐₓ values (from compute_h_max).
        :param support: dict mapping node ID -> predecessor node ID.
        :param goal_ids: Iterable of goal node IDs.
        :param hmax_value: the overall hₘₐₓ value (typically, max_{g in goal_ids} cost[g]).
        :return: A set of node IDs (of operator nodes) forming the landmark cut.
        """
        cut = set()
        queue = deque()
        visited = set()
        
        # Initialize the queue with goal nodes having cost equal to hmax_value.
        for gid in goal_ids:
            if cost.get(gid, math.inf) == hmax_value:
                queue.append(gid)
                
        while queue:
            curr_id = queue.popleft()
            if curr_id in visited:
                continue
            visited.add(curr_id)
            curr_node = self.graph.nodes[curr_id]
            # If an operator node with positive local cost is encountered, add to cut.
            if (curr_node.type == NodeType.AND and 
                self.local_costs.get(curr_id, 0) > 0):
                cut.add(curr_id)
                continue
            # Otherwise, follow the support pointer if available.
            if curr_id in support:
                pred_id = support[curr_id]
                queue.append(pred_id)
        return cut

    def compute_lm_cut(self, goal_ids):
        """
        Compute the LM-Cut heuristic over the RC graph for the given goal nodes.
        
        :param goal_ids: Iterable of node IDs representing the goal facts.
        :return: Tuple (h, landmarks)
          - h: the LM-Cut heuristic value (number, or math.inf if unreachable).
          - landmarks: a list of landmark cuts (each is a set of operator node IDs).
        """
        h = 0
        landmarks = []
        print(f'cut')
        while True:
            cost, support = self.compute_h_max(goal_ids)
            hmax_val = max(cost.get(gid, math.inf) for gid in goal_ids)
            if hmax_val == 0:
                # Goal reached.
                break
            if hmax_val == math.inf:
                # Goal is unreachable.
                return math.inf, landmarks

            cut = self.find_landmark_cut(cost, support, goal_ids, hmax_val)
            if not cut:
                break

            # λ is the minimum remaining cost among all operators in the cut.
            lam = min(self.local_costs[nid] for nid in cut)
            for nid in cut:
                self.local_costs[nid] -= lam
            h += lam
            landmarks.append(cut)
        self.lms = landmarks
        print(f'lmcut {landmarks}')
        exit(0)
        return h, landmarks
    
    def compute_lms(self):
        goals = [task.global_id for task in self.model.initial_tn]
        print(f'LMCuuuUT')
        self.compute_lm_cut(goals)
        
