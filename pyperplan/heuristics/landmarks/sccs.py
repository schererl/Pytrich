from collections import defaultdict, deque
import copy
class SCCDetection:
    def __init__(self, graph):
        self.graph = graph
        self.index = 0
        self.stack = []
        nodes = graph.fact_nodes + graph.task_nodes + graph.operator_nodes + graph.decomposition_nodes + [graph.init_node] + [graph.goal_node]
        num_nodes =  len(nodes) #initial and end nodes
        self.indices   = [-1] * num_nodes 
        self.low_links = [-1] * num_nodes
        self.on_stack  = [False] * num_nodes
        
        self.sccs = []
        self.node_to_scc = [-1] * num_nodes

        # Start the Tarjan's algorithm from each node if not already visited
        for node in nodes:
            if self.indices[node.ID] == -1:
                self._tarjan(node)
        
    def _tarjan(self, v):
        # Set the depth index for 'v' to the smallest unused index
        self.indices[v.ID] = self.index
        self.low_links[v.ID] = self.index
        self.index += 1
        self.stack.append(v)
        self.on_stack[v.ID] = True

        # Consider successors of 'v'
        for w in v.successor:
            if self.indices[w.ID] == -1:
                # Successor 'w' has not been visited; recurse on it
                self._tarjan(w)
                self.low_links[v.ID] = min(self.low_links[v.ID], self.low_links[w.ID])
            elif self.on_stack[w.ID]:
                # Successor 'w' is in the stack and hence in the current SCC
                self.low_links[v.ID] = min(self.low_links[v.ID], self.indices[w.ID])

        # If 'v' is a root node, pop the stack and generate an SCC
        if self.low_links[v.ID] == self.indices[v.ID]:
            current_scc = []
            while True:
                w = self.stack.pop()
                self.on_stack[w.ID] = False
                current_scc.append(w)
                self.node_to_scc[w.ID] = len(self.sccs)
                if w == v:
                    break
                
            self.sccs.append(current_scc)

    def initialize_reachability_structures(self):
        # structures for SCC and reachability
        self.scc2reachablenodes = [set() for _ in range(len(self.sccs))]
        self.finished = [False] * len(self.sccs)
        self.max_decomp_depth = [0] * len(self.sccs)
        
        # initialize sccs reachability
        for i, scc in enumerate(self.sccs):
            for node in scc:
                self.scc2reachablenodes[i].update([n.ID for n in node.successor])

        # for node in self.init_node.successor:
        #     scc_index = self.scc.node_to_scc[node.ID]
        #     print(scc_index)
        #     #if not self.finished[scc_index]:
        #     #    self.transitive_reachability(scc_index)
        scc_index = self.node_to_scc[self.graph.init_node.ID]
        self.transitive_reachability(scc_index)
        for scc_idx,scc_reach in enumerate(self.scc2reachablenodes):
            print(f'scc{scc_idx}:{self.sccs[scc_idx]} ==> {scc_reach}')

    def transitive_reachability(self, scc_index):
        reachable_nodes = copy.deepcopy(self.scc2reachablenodes[scc_index])
        max_depth = 0

        for node_id in reachable_nodes:
            node_scc_index = self.scc.node_to_scc[node_id]
            if node_scc_index != scc_index and not self.finished[node_scc_index]:
                self.transitive_reachability(node_scc_index)
            
            self.scc2reachablenodes[scc_index].update(self.scc2reachablenodes[node_scc_index])
            max_depth = max(max_depth, self.max_decomp_depth[node_scc_index])

        self.max_decomp_depth[scc_index] = max_depth + 1  # Increment depth for this level
        self.finished[scc_index] = True  