import time
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.ProblemRepresentation.and_or_graph import AndOrGraph, ContentType, NodeType
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model

class TaskDecompositionHeuristic(Heuristic):
    def __init__(self, use_satis=False, name="tdg"):
        super().__init__(name=name)
        self.use_satis = use_satis
        self.tdg_values = {}
        self.iterations = 0
        self.preprocessing_time = 0
        self.and_or_graph=None

    def initialize(self, model, initial_node):
        """
        Initialize the heuristic with the model and compute task decomposition graph.
        """
        start_time = time.time()
        self.and_or_graph = AndOrGraph(model, graph_type=3)
        self._compute_tdg()
        self.preprocessing_time = time.time() - start_time

        for node in self.and_or_graph.nodes:
            if node and node.content_type in \
                {ContentType.OPERATOR, ContentType.ABSTRACT_TASK}:
                self.tdg_values[node.ID] = node.value

        h_value = sum(self.tdg_values.get(task.global_id, float('inf')) \
                      for task in initial_node.task_network)
        
        return super().initialize(model, h_value)

    def _compute_tdg(self):
        """
        Iteratively compute values for the AND/OR graph using a bottom-up approach.
        """
        for node in self.and_or_graph.nodes:
            if not node:
                continue
            if node.content_type == ContentType.OPERATOR:
                node.value = 0
            else:
                node.value = 1 if self.use_satis and \
                node.content_type == ContentType.ABSTRACT_TASK \
                else float('inf')

        changed = True
        while changed:
            self.iterations += 1
            changed = False

            for node in self.and_or_graph.nodes:
                if not node:
                    continue

                new_value = node.weight
                if node.type == NodeType.OR:
                    new_value += min(n.value for n in node.predecessors)
                elif node.type == NodeType.AND:
                    new_value += sum(n.value for n in node.predecessors)

                if new_value != node.value:
                    changed = True
                    node.value = new_value

    def __call__(self, parent_node, node):
        h_value = sum(self.tdg_values.get(task.global_id, float('inf')) \
                      for task in node.task_network)
        super().update_info(h_value)
        return h_value
    
    def __repr__(self):
        str_output= "TDG("
        if self.use_satis:
            str_output+= "use_satis"
        str_output+= ")"
        return str_output
    
    def __str__(self):
        str_output= "TDG("
        if self.use_satis:
            str_output+= "use_satis"
        str_output+= ")"
        return str_output

    def __output__(self):
        return (
            f"Heuristic info:\n"
            f"\tName: {self.name}\n"
            f"\tGraph size: {len(self.tdg_values)}\n"
            f"\tIterations: {self.iterations}\n"
            f"\tPreprocessing time: {self.preprocessing_time:.2f} s\n"
        )