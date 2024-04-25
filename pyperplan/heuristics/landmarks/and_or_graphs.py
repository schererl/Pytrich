from enum import Enum, auto
from collections import deque, defaultdict
#from .sccs import SCCDetection
import time


#from ...model import Operator, Decomposition

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
        self.ID = ID
        self.type      = node_type
        self.weight    = weight
        self.successors   = []
        self.predecessors = []
        self.forced_true = False
        self.num_forced_predecessors = 0
        self.label = label

        self.content_type = content_type
        self.content = content
        
        
    def __str__(self):
        return "Node " + self.label + " " + ("T" if self.num_forced_predecessor else "F") + "("+str(len(self.predecessor))+","+str(len(self.successor))+")"
    def __repr__(self) -> str:
        return f"<Node {self.label}>"
    
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
    scc = None
    reachable_operators=[]
    

    # helper variables
    task_to_index = {} #change this
    op_to_index   = {} #change this add a unique identifier to operators, abstract tasks and methods
    ID_count=0
    def __init__(self, model, debug=True):
        # if not debug:
        #     self.initialize(model)
        # else:
        #     self.test_and_or_graph()
        #self.test_and_or_graph()
        self._and_or_test()

    def _and_or_test(self):
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

        nodeA = AndOrGraphNode(2, NodeType.AND, label="oA")
        nodeB = AndOrGraphNode(3, NodeType.AND, label="oB")

        nodeX = AndOrGraphNode(4, NodeType.OR, label="fx")
        nodeZ = AndOrGraphNode(5, NodeType.OR, label="fz")

        nodeM1 = AndOrGraphNode(6, NodeType.AND, label="M1")
        nodeM2 = AndOrGraphNode(7, NodeType.AND, label="M2")
        nodeM3 = AndOrGraphNode(8, NodeType.AND, label="M3")

        nodeT = AndOrGraphNode(9, NodeType.OR, label="T")
        nodeS = AndOrGraphNode(10, NodeType.OR, label="S")

        self.add_edge(nodeX, nodeA)
        self.add_edge(nodeA, nodeZ)
        self.add_edge(nodeZ, nodeB)
        self.add_edge(nodeT, nodeM1)
        self.add_edge(nodeT, nodeM2)        
        self.add_edge(nodeS, nodeM3)
        self.add_edge(nodeM1, nodeS)
        self.add_edge(nodeM1, nodeA)
        self.add_edge(nodeM2, nodeB)
        self.add_edge(nodeM3, nodeA)
        self.fact_nodes = [nodeX, nodeZ]
        self.task_nodes = [nodeT, nodeS]
        self.decomposition_nodes = [nodeM1, nodeM2, nodeM3]
        self.operator_nodes = [nodeA, nodeB]
        print(f'it worked')
        
    def test_and_or_graph(self):
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

        self.ID_count=14
        self.decomposition_nodes = [d1, d2, d3, d4, d5]
        self.task_nodes = [t1, t2, t3]
        self.operator_nodes = [o2, o3, end, done]
        self.fact_nodes = []
        
    # def initialize(self, model):
    #     self.init_node  = AndOrGraphNode(0, NodeType.AND, label='INIT')
    #     self.goal_node  = AndOrGraphNode(1, NodeType.AND, label='GOAL')
    #     self.ID_count=2

    #     number_facts = len(model.facts)
    #     self.fact_nodes=[None]*number_facts

    #     # set facts
    #     for fact_pos in range(number_facts):
    #         fact_node = AndOrGraphNode(self.ID_count, NodeType.OR, content_type=ContentType.FACT, content=fact_pos, label=model._int_to_explicit[fact_pos])
    #         self.ID_count+=1
    #         self.fact_nodes[fact_pos] = fact_node
            
    #         # set initial and goal nodes
    #         if model.initial_state & (1 << fact_pos):
    #             self.add_edge(self.init_node, fact_node)
                
    #         if model.goals & (1 << fact_pos):
    #             self.add_edge(fact_node, self.goal_node)
                
        
    #     # set task and methods
    #     for t_id, t in enumerate(model.abstract_tasks):
    #         task_node = AndOrGraphNode(self.ID_count, NodeType.OR, weight=1, label='task: '+t.name)
    #         self.ID_count+=1
    #         self.task_nodes.append(task_node)
    #         self.task_to_index[t]=t_id
            
    #     # set intial task network
    #     for init_t in model.initial_tn:
    #         task_id = self.task_to_index[init_t]
    #         self.add_edge(self.init_node, self.task_nodes[task_id])

    #     # set operators
    #     for op_i, op in enumerate(model.operators):    
    #         operator_node = AndOrGraphNode(self.ID_count, NodeType.AND, content_type=ContentType.OPERATOR, content=op_i, weight=1, label='op: '+op.name)
    #         self.ID_count+=1
    #         self.operator_nodes.append(operator_node)
    #         self.op_to_index[op] = op_i
    #         for fact_pos in range(number_facts):
    #             if op.pos_precons_bitwise & (1 << fact_pos):
    #                 var_node = self.fact_nodes[fact_pos]
    #                 self.add_edge(var_node, operator_node)
    #             elif op.neg_precons_bitwise & (1 << fact_pos):
    #                 var_node = self.fact_nodes[fact_pos]
    #                 self.add_edge(var_node, operator_node)
                
    #             if op.add_effects_bitwise & (1 << fact_pos):
    #                 var_node = self.fact_nodes[fact_pos]
    #                 self.add_edge(operator_node, var_node)

    #     # set methods
    #     for d_i, d in enumerate(model.decompositions):
    #         decomposition_node = AndOrGraphNode(self.ID_count, NodeType.AND, content_type=ContentType.METHOD, content=d_i, label='decomp: '+d.name)
    #         self.ID_count+=1
    #         self.decomposition_nodes.append(decomposition_node)
    #         task_head_id = self.task_to_index[d.compound_task]
    #         self.add_edge(self.task_nodes[task_head_id], decomposition_node)
            
    #         for fact_pos in range(number_facts):
    #             if d.pos_precons_bitwise & (1 << fact_pos):
    #                 var_node = self.fact_nodes[fact_pos]
    #                 self.add_edge(var_node, decomposition_node)
    #             elif d.neg_precons_bitwise & (1 << fact_pos):
    #                 var_node = self.fact_nodes[fact_pos]
    #                 self.add_edge(var_node, decomposition_node)
            
    #         for subt in d.task_network:
    #             subt_node = None
    #             if type(subt) is Operator:
    #                 subt_node = self.operator_nodes[self.op_to_index[subt]]
    #             else:
    #                 subt_node = self.task_nodes[self.task_to_index[subt]]
    #             self.add_edge(decomposition_node, subt_node)
        
        
    def add_edge(self, nodeA, nodeB):
        nodeA.successors.append(nodeB)
        nodeB.predecessors.append(nodeA)
    
    

        
