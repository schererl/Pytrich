from enum import Enum, auto
from collections import deque, defaultdict
from .sccs import SCCDetection #not used for now
import time
from ...model import Operator, Decomposition

class NodeType(Enum):
    AND = auto()
    OR = auto()

class ContentType(Enum):
    OPERATOR = auto()
    ABSTRACT_TASK = auto()
    METHOD = auto()
    FACT = auto()
    Nan = auto()


class AndOrGraphNode:
    def __init__(self, ID, node_type, content_type=ContentType.Nan, content="", weight=0, label=''):
        self.ID = ID # equal to model's global id
        self.type      = node_type
        self.weight    = weight
        self.successors   = []
        self.predecessors = []
        self.forced_true = False
        self.num_forced_predecessors = 0
        self.label = label

        self.content_type = content_type
        self.content = content # equal to position into model's type of content
        
        
    def __str__(self):
        return F"Node ID={self.ID} label={self.label}"
    def __repr__(self) -> str:
        return f"<Node {self.ID} {self.label}>"
    
class AndOrGraph:
    # and_or nodes
    nodes = []
    fact_nodes=[] #useful for using as starting point in landmarks
    
    # graph variables
    init_node = None
    goal_node = None
    init_tn   = []
    scc = None
    reachable_operators=[]
    
    def __init__(self, model, use_landmarks=True, debug=False):
        if not debug:
            self.initialize(model, use_landmarks=use_landmarks)
        else:
            self._and_or_test2()
            
            
        
    def initialize(self, model, use_landmarks=True):
        self.nodes = [None] * (len(model.facts) + len(model.operators) + len(model.abstract_tasks) + len(model.decompositions) + 2)
        self.init_node  = AndOrGraphNode(len(self.nodes)-2, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(len(self.nodes)-1, NodeType.AND, label='GOAL')
        
        self.nodes[self.init_node.ID] = self.init_node
        self.nodes[self.goal_node.ID] = self.goal_node

        number_facts = len(model.facts)
        self.fact_nodes=[None]*number_facts
        # set facts
        for fact_pos in range(number_facts):
            fact_node = AndOrGraphNode(fact_pos, NodeType.OR, content_type=ContentType.FACT, content=fact_pos, label=f'fact: {model._int_to_explicit[fact_pos]}')
            self.nodes[fact_pos]      = fact_node
            self.fact_nodes[fact_pos] = fact_node

            # removed for landmarks
            # set initial and goal nodes
            #if not use_landmarks and model.initial_state & (1 << fact_pos):
            #    self.add_edge(self.init_node, fact_node)
                
            #if not use_landmarks and model.goals & (1 << fact_pos):
            #    self.add_edge(fact_node, self.goal_node)
                
        # set task and methods
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(t.global_id, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, content=t_i, weight=1, label='task: '+t.name)
            self.nodes[t.global_id]=task_node

            
        # set intial task network
        for init_t in model.initial_tn:
            if not use_landmarks:
                self.add_edge(self.init_node, self.nodes[init_t.global_id])
            else:
                self.add_edge(self.nodes[init_t.global_id], self.init_node)

        # set operators
        for op_i, op in enumerate(model.operators):  
            operator_node = AndOrGraphNode(op.global_id, NodeType.AND, content_type=ContentType.OPERATOR, content=op_i, weight=1, label='op: '+op.name)
            self.nodes[op.global_id] = operator_node
            
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
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrGraphNode(d.global_id, NodeType.AND, content_type=ContentType.METHOD, content=d_i, label='decomp: '+d.name)
            self.nodes[d.global_id] = decomposition_node
            
            task_head_id = d.compound_task.global_id
            if not use_landmarks:
                self.add_edge(self.nodes[task_head_id], decomposition_node)
            else:
                self.add_edge(decomposition_node, self.nodes[task_head_id])
            
            for fact_pos in range(number_facts):
                if d.pos_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)
                elif d.neg_precons_bitwise & (1 << fact_pos):
                    var_node = self.fact_nodes[fact_pos]
                    self.add_edge(var_node, decomposition_node)
            
            for subt in d.task_network:
                subt_node = self.nodes[subt.global_id]
                if not use_landmarks:
                    self.add_edge(decomposition_node, subt_node)
                else:
                    self.add_edge(subt_node, decomposition_node)
            
    def add_edge(self, nodeA, nodeB):
        nodeA.successors.append(nodeB)
        nodeB.predecessors.append(nodeA)
    
    def search_node_id(self, string_label):
        for n in self.nodes:
            if string_label in n.label:
                return n.ID
        return -1

    def _and_or_test2(self):
        '''
        m1: <S, a>
        m2: <S, b>
        m3: <T, c>
        m4: <T, d>

        a: <x, y>
        b: <x, z>
        c: <x, z>
        d: <x, >
        e: <y and z, >

        TNI = (T,S,e)
        '''
        self.init_node  = AndOrGraphNode(0, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(1, NodeType.AND, label='GOAL') 
        M1 = AndOrGraphNode(2, NodeType.AND, label="M1")
        M2 = AndOrGraphNode(3, NodeType.AND, label="M2")
        M3 = AndOrGraphNode(4, NodeType.AND, label="M3")
        M4 = AndOrGraphNode(5, NodeType.AND, label="M4")

        A = AndOrGraphNode(6, NodeType.AND, label="oA")
        B = AndOrGraphNode(7, NodeType.AND, label="oB")
        C = AndOrGraphNode(8, NodeType.AND, label="oC")
        D = AndOrGraphNode(9, NodeType.AND, label="oD")
        E = AndOrGraphNode(10, NodeType.AND, label="oE")

        X = AndOrGraphNode(11, NodeType.OR, label="fx")
        Y = AndOrGraphNode(12, NodeType.OR, label="fy")
        Z = AndOrGraphNode(13, NodeType.OR, label="fz")

        T = AndOrGraphNode(14, NodeType.OR, label="T")
        S = AndOrGraphNode(15, NodeType.OR, label="S")
        self.fact_nodes = [X, Y, Z]
        self.task_nodes = [T, S]
        self.decomposition_nodes = [M1, M2, M3, M4]
        self.operator_nodes = [A, B, C, D, E]
        self.nodes = [None] * (len(self.fact_nodes) + len(self.task_nodes) + len(self.decomposition_nodes) + len(self.operator_nodes)+2)
        for n in self.fact_nodes + self.task_nodes + self.decomposition_nodes + self.operator_nodes + [self.init_node, self.goal_node]:
            self.nodes[n.ID] = n

        # setting m1
        self.add_edge(M1,S)
        self.add_edge(A,M1)
        self.add_edge(X,A)
        self.add_edge(A,Y)
        # setting m2
        self.add_edge(M2,S)
        self.add_edge(B,M2)
        self.add_edge(X,B)
        self.add_edge(B,Z)
        # setting m3
        self.add_edge(M3,T)
        self.add_edge(C,M3)
        self.add_edge(X,C)
        self.add_edge(C,Z)
        # setting m4
        self.add_edge(M4,T)
        self.add_edge(D,M4)
        self.add_edge(X,D)
        #setting e
        self.add_edge(Y, E)
        self.add_edge(Z, E)
        
    def _and_or_test1(self):
        '''
        oA: <x,z>
        oB: <z,>
        
        m1 : T -> S
               -> oA
        
        m2 : T -> oB

        m3 : S -> oA

        '''
        self.init_node  = AndOrGraphNode(0, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(1, NodeType.AND, label='GOAL') 

        A = AndOrGraphNode(2, NodeType.AND, label="oA")
        B = AndOrGraphNode(3, NodeType.AND, label="oB")

        X = AndOrGraphNode(4, NodeType.OR, label="fx")
        Z = AndOrGraphNode(5, NodeType.OR, label="fz")

        M1 = AndOrGraphNode(6, NodeType.AND, label="M1")
        M2 = AndOrGraphNode(7, NodeType.AND, label="M2")
        M3 = AndOrGraphNode(8, NodeType.AND, label="M3")

        T = AndOrGraphNode(9, NodeType.OR, label="T")
        S = AndOrGraphNode(10, NodeType.OR, label="S")

        
        self.add_edge(M1, T)
        self.add_edge(M2, T)        
        
        self.add_edge(S, M1)
        self.add_edge(B, M1)
        
        self.add_edge(B, M2)
        
        self.add_edge(M3, S)
        self.add_edge(A, M3)
        
        self.add_edge(X, A)
        self.add_edge(A, Z)
        self.add_edge(Z, B)
        
        self.fact_nodes = [X, Z]
        self.task_nodes = [T, S]
        self.decomposition_nodes = [M1, M2, M3]
        self.operator_nodes = [A, B]
        
        self.nodes = [None] * (len(self.fact_nodes) + len(self.task_nodes) + len(self.decomposition_nodes) + len(self.operator_nodes)+2)
        for n in self.fact_nodes + self.task_nodes + self.decomposition_nodes + self.operator_nodes + [self.init_node, self.goal_node]:
            self.nodes[n.ID] = n
        exit()
        
    def _and_or_test3(self):
        self.init_node  = AndOrGraphNode(0, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(1, NodeType.AND, label='GOAL')
        '''
                 T1 (init)
                /  \
               /    \
              D1     D2  
             / \      |
            T2 end    T3
           /  \       |
          D3    D4    D5  
         / \   /  \   | \
        T2 o2 o3  T1  T3 done (goal)
        '''
        t1  =  AndOrGraphNode(2,  NodeType.OR, label='T1')
        t2  =  AndOrGraphNode(3,  NodeType.OR, label='T2')
        t3  =  AndOrGraphNode(4,  NodeType.OR, label='T3')
        d1  =  AndOrGraphNode(5, NodeType.AND, label='D1')
        d2  =  AndOrGraphNode(6, NodeType.AND, label='D2')
        d3  =  AndOrGraphNode(7, NodeType.AND, label='D3')
        d4  =  AndOrGraphNode(8, NodeType.AND, label='D4')
        d5  =  AndOrGraphNode(9, NodeType.AND, label='D5')
        o2  =  AndOrGraphNode(10, NodeType.AND, label='O2')
        o3  =  AndOrGraphNode(11, NodeType.AND, label='O3')
        end  = AndOrGraphNode(12, NodeType.AND, label='end')
        done = AndOrGraphNode(13, NodeType.AND, label='done')
        
        self.add_edge(self.init_node, t1)
        self.add_edge(t1,d1)
        self.add_edge(t1,d2)

        self.add_edge(d1,t2)
        self.add_edge(d1,end)
        
        self.add_edge(d2,t3)
        self.add_edge(t3,d5)
        self.add_edge(d5,t3)
        self.add_edge(d5,done)
        
        self.add_edge(t2,d3)
        self.add_edge(t2,d4)
        
        self.add_edge(d3,t2)
        self.add_edge(d3,o2)
        
        self.add_edge(d4,o3)
        self.add_edge(d4,t1)
        
        self.add_edge(end, self.goal_node)

        self.decomposition_nodes = [d1, d2, d3, d4, d5]
        self.task_nodes = [t1, t2, t3]
        self.operator_nodes = [o2, o3, end, done]
        self.fact_nodes = []
        self.nodes = [None] * (len(self.fact_nodes) + len(self.task_nodes) + len(self.decomposition_nodes) + len(self.operator_nodes)+2)
        for n in self.fact_nodes + self.task_nodes + self.decomposition_nodes + self.operator_nodes + [self.init_node, self.goal_node]:
            self.nodes[n.ID] = n
        
        exit()
    
    

        
