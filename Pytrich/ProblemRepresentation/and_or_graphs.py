from enum import Enum, auto
from collections import deque

class NodeType(Enum):
    AND = auto()
    OR = auto()
    INIT = auto()

class ContentType(Enum):
    OPERATOR = auto()
    ABSTRACT_TASK = auto()
    METHOD = auto()
    FACT = auto()
    Nan = auto()


class AndOrGraphNode:
    def __init__(self, ID, node_type, content_type=ContentType.Nan, content="", weight=0, label=''):
        self.ID = ID   # equal to model's global id
        self.type      = node_type
        self.weight    = weight
        self.value     = 0
        self.successors   = []
        self.predecessors = []
        self.forced_true = False
        self.num_forced_predecessors = 0
        self.label = label

        self.content_type = content_type
        self.content = content  # equal to position into model's type of content
        
    def __str__(self):
        return F"Node ID={self.ID} label={self.label}"
    def __repr__(self) -> str:
        return f"<Node {self.ID} {self.label}>"
    
class AndOrGraph:
    # graph variables
    init_node = None
    goal_node = None
    scc = None # not working
    
    def __init__(self, model, use_top_down=True, use_tdg_only=False):
        self.i_node_set = set()
        self.counter = 0
        self.use_top_down = use_top_down
        self.use_tdg_only = use_tdg_only
        self.initialize(model)
        
        
    def initialize(self, model):
        self.nodes = [None] * (len(model.facts) + len(model.operators) + len(model.abstract_tasks) + len(model.decompositions) + 2)
        self.init_node  = AndOrGraphNode(len(self.nodes)-2, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(len(self.nodes)-1, NodeType.AND, label='GOAL')
        
        self.nodes[self.init_node.ID] = self.init_node
        self.nodes[self.goal_node.ID] = self.goal_node

        number_facts = len(model.facts)
        self.fact_nodes=[None]*number_facts
        
        # set facts
        if not self.use_tdg_only:
            for fact_pos in range(number_facts):
                fact_node = AndOrGraphNode(fact_pos, NodeType.OR, content_type=ContentType.FACT, content=fact_pos, label=f'{model.get_fact_name(fact_pos)}')
                self.nodes[fact_pos]      = fact_node
                self.fact_nodes[fact_pos] = fact_node
                if model.initial_state & (1 << fact_pos):
                    fact_node.type = NodeType.INIT
                    self.i_node_set.add(fact_pos)
        
        # set abstract task
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(t.global_id, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, content=t_i, weight=1, label=t.name)
            self.nodes[t.global_id]=task_node
            
        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):  
            operator_node = AndOrGraphNode(op.global_id, NodeType.AND, content_type=ContentType.OPERATOR, content=op_i, weight=1, label=op.name)
            self.nodes[op.global_id] = operator_node
            
            if not self.use_tdg_only:
                for fact_pos in range(number_facts):
                    if op.pos_precons_bitwise & (1 << fact_pos):
                        var_node = self.fact_nodes[fact_pos]
                        self.add_edge(var_node, operator_node)
                    
                    if op.add_effects_bitwise & (1 << fact_pos):
                        var_node = self.fact_nodes[fact_pos]
                        self.add_edge(operator_node, var_node)

        
        # set methods
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrGraphNode(d.global_id, NodeType.AND, content_type=ContentType.METHOD, content=d_i, label=d.name)
            self.nodes[d.global_id] = decomposition_node
            task_head_id = d.compound_task.global_id
            if self.use_top_down:
                self.add_edge(self.nodes[task_head_id], decomposition_node)
            else:
                self.add_edge(decomposition_node, self.nodes[task_head_id])
            
            
            for subt in d.task_network:
                subt_node = self.nodes[subt.global_id]
            
                if self.use_top_down:
                    self.add_edge(decomposition_node, subt_node)
                else:
                    self.add_edge(subt_node, decomposition_node)
                
            if not self.use_tdg_only:
                for fact_pos in range(number_facts):
                    if d.pos_precons_bitwise & (1 << fact_pos):
                        fact_node = self.fact_nodes[fact_pos]
                        self.add_edge(fact_node, decomposition_node)
        
        # NOTE: still not sure what are the implicatons of it
        if self.use_top_down:
            for task in model.initial_tn:
                self.nodes[task.global_id].type= NodeType.INIT
                self.i_node_set.add(task.global_id)
        
        if not self.use_tdg_only:
            # erase predecessors from initial facts
            for i_node in self.i_node_set:
                node = self.nodes[i_node]
                # if is a task, it won't require to be enabled by some decomposition
                if node.content_type == ContentType.OPERATOR or node.content_type == ContentType.ABSTRACT_TASK:
                    for pred in node.predecessors[:]:
                        if pred.content_type == ContentType.METHOD:
                            self.remove_edge(pred, node)
                else:
                    for pred in node.predecessors[:]: #NOTE: use the '[:]' to avoid changing the list while iterating it
                        self.remove_edge(pred, node)
                
            
    def add_edge(self, nodeA, nodeB):
        nodeA.successors.append(nodeB)
        nodeB.predecessors.append(nodeA)
    
    def remove_edge(self, nodeA, nodeB):
        nodeA.successors.remove(nodeB)
        nodeB.predecessors.remove(nodeA)
    
    # utils function
    def search_node_id(self, string_label):
        for n in self.nodes:
            if string_label in n.label:
                return n.ID
        return -1