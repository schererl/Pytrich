from .heuristic import Heuristic
from ..model import Operator, AbstractTask
from ..utils import UNSOLVABLE
from .landmarks.and_or_graphs import AndOrGraph, NodeType
from collections import deque 

'''
    Use a AndOr graph to perform a reachability analysis into a htn problem.
    Check if goal node is reachable (set of facts)
'''
class ReachabilityHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
        self.andor_graph = None
        
    def compute_heuristic(self, model, parent_node, task, state, task_network):
        if not parent_node:
            self.andor_graph.clear_andor_grap()
            self.andor_graph.update_init_node(state, task_network)
        else:
            self.andor_graph = AndOrGraph(model)
        
        return self.check_reachability()
    
    def check_reachability(self):
        reachable_nodes = deque()
        reachable_nodes.append(self.andor_graph.init_node)
        while reachable_nodes:
            node = reachable_nodes.pop(0)
            if node.forced_true:
                continue
            node.forced_true=True
            for succ in node.successors:
                succ.num_forced_predecessor+=1
                if succ.type == NodeType.OR or (succ.type == NodeType.AND and succ.num_forced_predecessor == len(succ.predecessors)):
                    if succ == self.andor_graph.goal_node:
                        return True
                    reachable_nodes.append(succ)
        return self.check_fully_decomposable(self.andor_graph.init_node)

    def check_fully_decomposable(self, node):
        '''
        Check if the abstract tasks could be entirelly decomposed
        '''
        if not node.forced_true:
            return False
        if len(node.successors)==0:
            return True
        
        
        for succ in node.successors:
            result = self.check_fully_decomposable(succ)
            if node.type == NodeType.OR and result is True:
                return True
            elif node.type == NodeType.AND and result is False:
                return False
        return True


    def update_init_node(self, state, task_network):
        for succ in self.andor_graph.init_node.successor:
            succ.predecessor.remove(self.init_node)

        self.andor_graph.init_node.successor = []
        for fact_pos in range(len(self.andor_graph.fact_nodes)):
            if state & (1 << fact_pos):
                fact_node = self.fact_nodes[fact_pos]
                self.andor_graph.add_edge(self.init_node, fact_node)

        for t in task_network:
            task_node=None
            if type(t) is Operator:
                task_node = self.andor_graph.operator_nodes[self.andor_graph.op_id_nodes[t]]
            else:
                task_node = self.andor_graph.task_nodes[self.andor_graph.task_id_nodes[t]]
            self.andor_graph.add_edge(self.andor_graph.init_node, task_node)

    def clear_andor_graph(self):
        self.andor_graph.goal_node.forced_true=False
        self.andor_graph.goal_node.num_forced_predecessor=0
        
        self.andor_graph.init_node.forced_true=False
        self.andor_graph.init_node.num_forced_predecessor=0
        
        for n_f in self.fact_nodes:
            n_f.andor_graph.forced_true=False
            n_f.andor_graph.num_forced_predecessor=0
        
        for n_op in self.operator_nodes:
            n_op.andor_graph.forced_true=False
            n_op.andor_graph.num_forced_predecessor=0
        
        for n_d in self.decomposition_nodes:
            n_d.andor_graph.forced_true=False
            n_d.andor_graph.num_forced_predecessor=0
        
        for n_t in self.task_nodes:
            n_t.andor_graph.forced_true=False
            n_t.andor_graph.num_forced_predecessor=0