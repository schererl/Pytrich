from enum import Enum, auto
from collections import deque, defaultdict
from ...model import Operator, Decomposition

class NodeType(Enum):
    AND = auto()
    OR = auto()


class AndOrGraphNode:
    def __init__(self, node_type, weight=0):
        self.type      = node_type
        self.weight    = weight
        self.successor   = []
        self.predecessor = []
        self.forced_true = False
        self.num_forced_successors = 0
    
        
        
class AndOrGraph:
    fact_nodes=[]
    operator_nodes=[]
    decomposition_nodes = []
    task_nodes = []

    init_node = []
    goal_node = []
    init_tn   = []

    task_id_nodes = {}
    op_id_nodes   = {}
    def __init__(self, model):
        self.init_node  = AndOrGraphNode(NodeType.AND)
        self.goal_node  = AndOrGraphNode(NodeType.AND)
        
        number_facts = len(model.facts)
        self.fact_nodes=[]
        # set facts
        for fact_pos in range(number_facts):
            var_node = AndOrGraphNode(NodeType.OR)
            self.fact_nodes.append(var_node)
            # set initial and goal nodes
            if model.initial_state & (1 << fact_pos):
                self.add_edge(self.init_node, var_node)
            if model.goals & (1 << fact_pos):
                self.add_edge(var_node, self.goal_node)
        
        # set task and methods
        for t_id, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(NodeType.OR, 1)
            self.task_nodes.append(task_node)
            self.task_id_nodes[t]=t_id
            
        # set intial task network
        for init_t in model.initial_tn:
            task_id = self.task_id_nodes[init_t]
            self.task_nodes[task_id].forced_true=True
            self.add_edge(self.init_node, task_node)

        # set operators
        for id_op, op in enumerate(model.operators):    
            operator_node = AndOrGraphNode(NodeType.AND, 1)
            self.operator_nodes.append(operator_node)
            self.op_id_nodes[op] = id_op
            for fact_pos in range(number_facts):
                if op.pos_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, operator_node)
                elif op.neg_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, operator_node)
                
                if op.add_effects_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(operator_node, var_node)

        # set methods
        for d in model.decompositions:
            decomposition_node = AndOrGraphNode(NodeType.AND)
            self.decomposition_nodes.append(decomposition_node)
            c_task_id = self.task_id_nodes[d.compound_task]
            self.add_edge(self.task_nodes[c_task_id], decomposition_node)
            
            for fact_pos in range(number_facts):
                if  op.pos_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)
                elif op.neg_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)

            for subt in d.task_network:
                subt_node = None
                if type(subt) is Operator:
                    subt_node = self.operator_nodes[self.op_id_nodes[subt]]
                else:
                    subt_node = self.task_nodes[self.task_id_nodes[d.compound_task]]
                self.add_edge(decomposition_node, subt_node)
                
    def add_edge(self, nodeA, nodeB):
        nodeA.successor.append(nodeB)
        nodeB.predecessor.append(nodeA)

    def check_rechability(self):
        process_queue = deque()
        process_queue.append(self.init_node)
        while process_queue:
            node = process_queue.popleft()
            for succ_node in node.successor:
                if succ_node.forced_true:
                    continue
                succ_node.num_forced_successors+=1
                if succ_node.type is NodeType.OR:
                    succ_node.forced_true=True
                    process_queue.append(succ_node)
                elif succ_node.num_forced_successors == len(succ_node.predecessor):
                    succ_node.forced_true=True
                    process_queue.append(succ_node)
                
                if succ_node.forced_true and succ_node == self.goal_node:
                    return 0
        return 100000000
                
    def update_init(self, current_state, current_task_network):
        for succ in self.init_node.successor:
            succ.predecessor.remove(self.init_node)
            self.init_node.successor.remove(succ)
        
        for fact_pos in range(len(self.fact_nodes)):
            var_node = AndOrGraphNode(NodeType.OR)
            self.fact_nodes.append(var_node)
            if current_state & (1 << fact_pos):
                self.add_edge(self.init_node, var_node)
        for t in current_task_network:
            task_node=None
            if type(t) is Operator:
                task_node = self.operator_nodes[self.op_id_nodes[t]]
            else:
                task_node = self.task_nodes[self.task_id_nodes[t]]
            self.add_edge(self.init_node, task_node)
            
    def clear(self):
        self.goal_node.forced_true=False
        for n_f in self.fact_nodes:
            n_f.forced_true=False
        for n_op in self.operator_nodes:
            n_op.forced_true=False
        for n_d in self.decomposition_nodes:
            n_d.forced_true=False
        for n_t in self.task_nodes:
            n_t.forced_true=False


            
    
    
