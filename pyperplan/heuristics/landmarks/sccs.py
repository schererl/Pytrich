from collections import defaultdict, deque

class SCCDetection:
    def __init__(self, graph):
        self.graph = graph
        self.index = 0
        self.stack = []
        num_nodes = max(node.ID for node in graph.fact_nodes + graph.task_nodes + graph.operator_nodes + graph.decomposition_nodes) + 1
        self.indices = [-1] * num_nodes 
        self.low_links = [-1] * num_nodes
        self.on_stack = [False] * num_nodes
        self.sccs = []

        # Start the Tarjan's algorithm from each node if not already visited
        for node in graph.fact_nodes + graph.task_nodes + graph.operator_nodes + graph.decomposition_nodes:
            if self.indices[node.ID] == -1:
                self.tarjan(node)
        
    def tarjan(self, v):
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
                self.tarjan(w)
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
                if w == v:
                    break
            self.sccs.append(current_scc)
