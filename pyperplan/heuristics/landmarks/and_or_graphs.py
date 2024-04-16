from enum import Enum, auto
from collections import deque, defaultdict
from ...model import Operator, Decomposition
import time
class NodeType(Enum):
    AND = auto()
    OR = auto()


class AndOrGraphNode:
    def __init__(self, ID, node_type, weight=0, label=''):
        self.ID = ID
        self.type      = node_type
        self.weight    = weight
        self.successor   = []
        self.predecessor = []
        self.forced_true = False
        self.num_forced_predecessor = 0
        self.label = label
        
        
    def __str__(self):
        return "Node " + self.label + " " + ("T" if self.num_forced_predecessor else "F") + "("+str(len(self.predecessor))+","+str(len(self.successor))+")"
    
class AndOrGraph:
    # and_or nodes
    fact_nodes=[]
    operator_nodes=[]
    decomposition_nodes = []
    task_nodes= []
    
    # graph variables
    init_node = None
    goal_node = None
    init_tn   = []

    # helper variables
    task_to_index = {}
    op_to_index   = {}
    ID_count=0
    def __init__(self, model):
        self.init_node  = AndOrGraphNode(NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(NodeType.AND, label='GOAL')
        
        number_facts = len(model.facts)
        self.fact_nodes=[None]*number_facts

        # set facts
        for fact_pos in range(number_facts):
            fact_node = AndOrGraphNode(self.ID_count, NodeType.OR, label=model._int_to_explicit[fact_pos])
            self.ID_count+=1
            self.fact_nodes[fact_pos] = fact_node
            
            # set initial and goal nodes
            if model.initial_state & (1 << fact_pos):
                self.add_edge(self.init_node, fact_node)
                
            if model.goals & (1 << fact_pos):
                self.add_edge(fact_node, self.goal_node)
                
        
        # set task and methods
        for t_id, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(self.ID_count, NodeType.OR, weight=1, label='task: '+t.name)
            self.ID_count+=1
            self.task_nodes.append(task_node)
            self.task_to_index[t]=t_id
            
        # set intial task network
        for init_t in model.initial_tn:
            task_id = self.task_to_index[init_t]
            self.add_edge(self.init_node, self.task_nodes[task_id])

        # set operators
        for id_op, op in enumerate(model.operators):    
            operator_node = AndOrGraphNode(self.ID_count, NodeType.AND, weight=1, label='op: '+op.name)
            self.ID_count+=1
            self.operator_nodes.append(operator_node)
            self.op_to_index[op] = id_op
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
            decomposition_node = AndOrGraphNode(self.ID_count, NodeType.AND, label='decomp: '+d.name)
            self.ID_count+=1
            self.decomposition_nodes.append(decomposition_node)
            task_head_id = self.task_to_index[d.compound_task]
            self.add_edge(self.task_nodes[task_head_id], decomposition_node)
            
            for fact_pos in range(number_facts):
                if d.pos_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)
                elif d.neg_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)
            
            for subt in d.task_network:
                subt_node = None
                if type(subt) is Operator:
                    subt_node = self.operator_nodes[self.op_id_nodes[subt]]
                else:
                    subt_node = self.task_nodes[self.task_id_nodes[subt]]
                self.add_edge(decomposition_node, subt_node)
        
                
    def add_edge(self, nodeA, nodeB):
        nodeA.successor.append(nodeB)
        nodeB.predecessor.append(nodeA)