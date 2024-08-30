import time
from Pyperplan.Heuristics.heuristic import Heuristic
from Pyperplan.ProblemRepresentation.and_or_graphs import AndOrGraph, ContentType, NodeType
from Pyperplan.Search.htn_node import HTNNode
from Pyperplan.model import Model

class TaskDecompositionHeuristic(Heuristic):
    def __init__(self, model:Model, initial_node:HTNNode, name="tdg"):
        super().__init__(model, initial_node, name=name)
        self.and_or_graph = AndOrGraph(model, use_top_down=False, use_tdg_only=True)
        self.iterations = 0
        init_time = time.time()
        self.tdg_values = {}
        self._compute_tdg()
        for n in self.and_or_graph.nodes:
            if n is None:
                continue
            if n != None and n.content_type == ContentType.OPERATOR or n.content_type == ContentType.ABSTRACT_TASK:
                self.tdg_values[n.ID] = n.value
        
        self.preprocessing_time = time.time() - init_time
        self.and_or_graph = None # remove and_or_graph for memory
        super().set_h_f_values(initial_node, sum([self.tdg_values[t.global_id] for t in initial_node.task_network]))
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


        changed=True
        while changed:
            self.iterations+=1
            changed=False
            for node in self.and_or_graph.nodes:
                if node is None:
                    continue
                new_value = node.weight
                if node.type == NodeType.OR:
                    new_value += min([n.value for n in node.predecessors])
                
                elif node.type == NodeType.AND:
                    new_value += sum([n.value for n in node.predecessors])
                    
                if new_value != node.value:
                    changed=True
                    node.value=new_value
                    
                     
    def __call__(self, parent_node, node):
        super().set_h_f_values(node, sum([self.tdg_values[t.global_id] for t in node.task_network]))
    
    def __output__(self):
        str_output = f'Heuristic info:\n\theuristic name: {self.name}\n\tGraph size: {len(self.tdg_values)}\n\tIterations: {self.iterations}\n\tPreprocessing time: {self.preprocessing_time:.2f} s\n'
        return str_output