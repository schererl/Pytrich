from collections import deque
from pyperplan.heuristics.heuristic import Heuristic
from pyperplan.heuristics.landmarks.and_or_graphs import AndOrGraph, ContentType, NodeType
from pyperplan.heuristics.landmarks.landmark import Landmarks

class TaskDecompositionHeuristic(Heuristic):
    def __init__(self, model, initial_node, name="tdg"):
        super().__init__(model, initial_node, name=name)
        self.and_or_graph = AndOrGraph(model, use_top_down=False, use_tdg_only=True)
        self._compute_tdg()
        
        super().set_hvalue(initial_node, sum([self.and_or_graph.nodes[t.global_id].value for t in initial_node.task_network]))
        self.initial_h = initial_node.h_value
        

    def _compute_tdg(self):
        starting_nodes = []
        for node in self.and_or_graph.nodes:
            if node is None:
                continue
            if node.content_type == ContentType.OPERATOR:
                starting_nodes.append(node)
                node.weight = 1
                node.value = 0
            else:
                node.weight = 0
                node.value = 10000000


        #queue = deque(starting_nodes)
        changed=True
        while changed:
            changed=False
            for node in self.and_or_graph.nodes:
                if node is None:
                    continue
            #node = queue.popleft()
                new_value = node.weight
                if node.type == NodeType.OR:
                    new_value += min([n.value for n in node.predecessors])
                
                elif node.type == NodeType.AND:
                    new_value += sum([n.value for n in node.predecessors])
                    
                if new_value != node.value:
                    changed=True
                    node.value=new_value
                    
                     
                #     for succ in node.successors:
                #         queue.append(succ)

    def compute_heuristic(self, parent_node, node):
        super().set_hvalue(node, sum([self.and_or_graph.nodes[t.global_id].value for t in node.task_network]))
       