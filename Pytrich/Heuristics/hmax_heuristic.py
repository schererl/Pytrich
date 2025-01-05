import time
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.ProblemRepresentation.and_or_graph import AndOrGraph, ContentType, NodeType
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model, Operator
import math

'''
    UNDER DEVELOPMENT
'''

class HmaxHeuristic(Heuristic):
    def __init__(self, model: Model, initial_node: HTNNode, name="hmax_htn"):
        pass
    #     super().__init__(model, initial_node, name=name)
    #     self.and_or_graph = AndOrGraph(model, graph_type=4)  
        
    #     init_time = time.time()
    #     self.h_values = {}
    #     self._compute_hmax()

    #     initial_estimate = sum([self.h_values[t.global_id] for t in initial_node.task_network])
    #     super().set_h_f_values(initial_node, initial_estimate)
    #     self.initial_h = initial_node.h_values[0]

    #     self.preprocessing_time = time.time() - init_time
        
    # def _compute_hmax(self):
        
    #     for node in self.and_or_graph.nodes:
    #         if node is None:
    #             continue
    #         if node.type == NodeType.INIT:
    #             node.value = 0
    #         else:
    #             node.value = math.inf

    #     changed = True
    #     iterations = 0
    #     while changed:
    #         changed = False
    #         iterations += 1
    #         for node in self.and_or_graph.nodes:
    #             if node is None:
    #                 continue
                
    #             old_value = node.value
    #             if node.type == NodeType.OR:
    #                 if node.predecessors:
    #                     new_value = min(p.value for p in node.predecessors)
    #                 else:
    #                     new_value = node.value  
    #             elif node.type == NodeType.AND:
    #                 if node.predecessors:
    #                     new_value = node.weight + max(p.value for p in node.predecessors)
    #                 else:
    #                     new_value = node.weight
    #             else:
    #                 new_value = node.value

    #             if new_value < old_value:
    #                 node.value = new_value
    #                 changed = True

    #     for n in self.and_or_graph.nodes:
    #         if n is None:
    #             continue
    #         if n.content_type in {ContentType.OPERATOR, ContentType.ABSTRACT_TASK, ContentType.FACT}:
    #             self.h_values[n.ID] = n.value

    # def __call__(self, parent_node: HTNNode, node: HTNNode):
    #     h_val = sum([self.h_values.get(t.global_id, math.inf) for t in node.task_network])
    #     return h_val

    # def __output__(self):
    #     str_output = f'Heuristic info:\n' \
    #                  f'\theuristic name: {self.name}\n' \
    #                  f'\tGraph size: {len(self.h_values)}\n' \
    #                  f'\tPreprocessing time: {self.preprocessing_time:.2f} s\n'
    #     return str_output
