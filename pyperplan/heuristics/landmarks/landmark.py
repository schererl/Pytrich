from collections import deque
#from .and_or_graphs import AndOrGraph, NodeType
from  and_or_graphs import AndOrGraph, NodeType #only for direct testing
class Landmarks:
    def __init__(self, and_or_graph):
        self.and_or_graph = and_or_graph
        self.nodes = [None]*( len(self.and_or_graph.fact_nodes)+len(self.and_or_graph.task_nodes)+len(self.and_or_graph.decomposition_nodes)+len(self.and_or_graph.operator_nodes)+2)
        self.landmarks = [None]*len(self.nodes)
        
        self.nodes[self.and_or_graph.init_node.ID]=self.and_or_graph.init_node
        self.nodes[self.and_or_graph.goal_node.ID]=self.and_or_graph.goal_node
        for f_n in self.and_or_graph.fact_nodes:
            self.nodes[f_n.ID] = f_n

        for d_n in self.and_or_graph.decomposition_nodes:
            self.nodes[d_n.ID] = d_n

        for o_n in self.and_or_graph.operator_nodes:
            self.nodes[o_n.ID] = o_n

        for t_n in self.and_or_graph.task_nodes:
            self.nodes[t_n.ID] = t_n

    def generate_lms(self):
        print(self.nodes)
        queue = deque(node for node in self.and_or_graph.fact_nodes if not node.successors)
        print(queue)
        done_lms = [0] * len(self.nodes)
        while queue:
            node = queue.popleft()
            print(node.ID)
            if self.landmarks[node.ID] != None:
                continue
            
            self.landmarks[node.ID] = {node.ID}
            if node.type == NodeType.OR:
                # OR node: intersection of all successors' landmarks
                new_landmarks = set.intersection(*(self.landmarks[succ.ID] for succ in node.successors))
            elif node.type == NodeType.AND:
                # AND node: union of all successors' landmarks
                new_landmarks = set.union(*(self.landmarks[succ.ID] for succ in node.successors))
            
            
            self.landmarks[node.ID].update(new_landmarks)

            for pred in node.predecessors:
                done_lms[pred.ID]+=1
                if done_lms == len(node.successors):
                    queue.append(pred)

if __name__ == '__main__':
    graph= AndOrGraph(None, debug=True)
    lm = Landmarks(graph)
    lm.generate_lms()
    print(lm.landmarks)

        
        