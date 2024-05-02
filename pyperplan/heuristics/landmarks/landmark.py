from collections import deque
from and_or_graphs import AndOrGraph, NodeType  # Ensure this is correctly imported

class Landmarks:
    def __init__(self, and_or_graph):
        self.and_or_graph = and_or_graph
        self.nodes = [None] * (len(self.and_or_graph.fact_nodes) + len(self.and_or_graph.task_nodes) +
                               len(self.and_or_graph.decomposition_nodes) + len(self.and_or_graph.operator_nodes) + 2)
        self.landmarks = [set()] * len(self.nodes)  # Initialize landmarks as empty sets
        
        
        self.nodes[self.and_or_graph.init_node.ID] = self.and_or_graph.init_node
        self.nodes[self.and_or_graph.goal_node.ID] = self.and_or_graph.goal_node
        for node_list in [self.and_or_graph.fact_nodes, self.and_or_graph.decomposition_nodes,
                          self.and_or_graph.operator_nodes, self.and_or_graph.task_nodes]:
            for node in node_list:
                self.nodes[node.ID] = node

    def generate_lms(self):
        fact_op_queue = deque([node for node in self.and_or_graph.fact_nodes if len(node.predecessors) == 0])
        hierarchical_queue = deque()
        #fact-operator lms
        while fact_op_queue:
            node = fact_op_queue.popleft()
            new_landmarks= set()
            if node.type == NodeType.OR and node.predecessors:
                new_landmarks = set.intersection(*(self.landmarks[pred.ID] for pred in node.predecessors))
                
            elif node.type == NodeType.AND and node.predecessors:
                new_landmarks = set.union(*(self.landmarks[pred.ID] for pred in node.predecessors))
            self.landmarks[node.ID] = new_landmarks | {node.ID}
            
            for succ in node.successors:
                if all(len(self.landmarks[pred.ID])!=None for pred in succ.predecessors):
                    fact_op_queue.append(succ)

        #hierarchical_queue
        while hierarchical_queue:
            node = hierarchical_queue.popleft()
            new_landmarks= set()
            if node.type == NodeType.OR and node.successors:
                new_landmarks = set.intersection(*(self.landmarks[pred.ID] for pred in node.successors))
                
            elif node.type == NodeType.AND and node.successors:
                new_landmarks = set.union(*(self.landmarks[pred.ID] for pred in node.successors))
            self.landmarks[node.ID] = new_landmarks | {node.ID}
            
            for succ in node.predecessors:
                if all(len(self.landmarks[pred.ID])!=None for pred in succ.successors):
                    hierarchical_queue.append(succ)

if __name__ == '__main__':
    graph = AndOrGraph(None, debug=True)  # Ensure correct initialization
    lm = Landmarks(graph)
    lm.generate_lms()
    for node_id, lms in enumerate(lm.landmarks):
        print(f"node{node_id} {lm.nodes[node_id]}")
        for lm_id in lms:
            print(f"\tlm {lm.nodes[lm_id]}")
