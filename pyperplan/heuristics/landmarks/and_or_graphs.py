from enum import Enum, auto
from collections import deque

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
        self.ID = ID   # equal to model's global id
        self.type      = node_type
        self.weight    = weight
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
    

    def __init__(self, model, top_down=True, debug=False):
        nodes = []
        reachable_operators=[]
        init_tn = []
        fact_nodes=[] #useful for using as landmark extraction starting point
        self.i_node_set = set()
        self.counter = 0
        if not debug:
            self.initialize(model, top_down=top_down)
        else:
            self._and_or_test1(top_down)
        
    def initialize(self, model, top_down=True):
        self.nodes = [None] * (len(model.facts) + len(model.operators) + len(model.abstract_tasks) + len(model.decompositions) + 2)
        self.init_node  = AndOrGraphNode(len(self.nodes)-2, NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(len(self.nodes)-1, NodeType.AND, label='GOAL')
        
        self.nodes[self.init_node.ID] = self.init_node
        self.nodes[self.goal_node.ID] = self.goal_node

        number_facts = len(model.facts)
        self.fact_nodes=[None]*number_facts
        # set facts
        for fact_pos in range(number_facts):
            fact_node = AndOrGraphNode(fact_pos, NodeType.OR, content_type=ContentType.FACT, content=fact_pos, label=f'{model._int_to_explicit[fact_pos]}')
            self.nodes[fact_pos]      = fact_node
            self.fact_nodes[fact_pos] = fact_node
            if model.initial_state & (1 << fact_pos):
                self.i_node_set.add(fact_pos)
        # set abstract task
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(t.global_id, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, content=t_i, weight=1, label=t.name)
            self.nodes[t.global_id]=task_node
            
        # still not sure what are the implicatons of it
        for task in model.initial_tn:
            self.i_node_set.add(task.global_id)

        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):  
            operator_node = AndOrGraphNode(op.global_id, NodeType.AND, content_type=ContentType.OPERATOR, content=op_i, weight=1, label=op.name)
            self.nodes[op.global_id] = operator_node
            
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
            if top_down:
                self.add_edge(self.nodes[task_head_id], decomposition_node)
            else:
                self.add_edge(decomposition_node, self.nodes[task_head_id])
                
            for subt in d.task_network:
                subt_node = self.nodes[subt.global_id]
                if top_down:
                    self.add_edge(decomposition_node, subt_node)
                else:
                    self.add_edge(subt_node, decomposition_node)
                    

            for fact_pos in range(number_facts):
                if d.pos_precons_bitwise & (1 << fact_pos):
                    fact_node = self.fact_nodes[fact_pos]
                    self.add_edge(fact_node, decomposition_node)
        
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
    
    #debug function
    def dot_output(self):
        import graphviz

        dot = graphviz.Digraph('AndOrGraph', format='svg')
        dot.attr(rankdir='LR')  
        dot.attr(splines='polyline')

        for node in self.nodes:
            if node is None:
                continue
            shape = 'circle' if node.type == NodeType.OR else 'box' 
            dot.node(str(node.ID), label=node.label, shape=shape)

        for node in self.nodes:
            if node is None or not node.successors:
                continue
            for succ in node.successors:
                dot.edge(str(node.ID), str(succ.ID))

        dot.render('andorgraph', cleanup=True)  
        print("Graph image saved as andorgraph.svg")

    # useful when cycle seems problematic
    def generate_cycle_blockworld_p2(self):
        import graphviz
        stack_b7_b4_ = self.search_node_id("op: stack_b7_b4_")
        putmdown_b4_ = self.search_node_id("putmdown_b4_")
        do_put_on_b7_b4_ = self.search_node_id("do_put_on_b7_b4_")
        pholding_b4_     = self.search_node_id("pholding_b4_")
        pclear_b4_       = self.search_node_id("pclear_b4_")
        
        src_dest_lst =  [
            (putmdown_b4_, do_put_on_b7_b4_),
            (stack_b7_b4_, do_put_on_b7_b4_),
            (stack_b7_b4_, putmdown_b4_),
            (putmdown_b4_, stack_b7_b4_),
            (do_put_on_b7_b4_, pholding_b4_),
            (pholding_b4_, do_put_on_b7_b4_),
            (putmdown_b4_, pholding_b4_),
            (pholding_b4_, putmdown_b4_),
            (pclear_b4_, stack_b7_b4_),
            (stack_b7_b4_, pclear_b4_)
        ]

        path_results = []
        for src, dest in src_dest_lst:
            path_results.append(self.find_path(src, dest))


        nodes_set = set()
        edges_set = set()
        for path, nodes in path_results:
            nodes_set.update(set(nodes))
            edges_set.update(set(path))
        
        dot = graphviz.Digraph('CyclePathBlocks02', format='svg')
        dot.attr(rankdir='LR')  
        dot.attr(splines='polyline')
        
        
        for node_id in nodes_set:
            node = self.nodes[node_id]
            if node is None:
                continue
            shape = 'circle' if node.type == NodeType.OR else 'box'
            dot.node(str(node.ID), label=node.label, shape=shape)

        
        for edges in edges_set:
            dot.edge(str(edges[0]), str(edges[1]))
        dot.render('Cycle/CyclePathBlocks02', cleanup=True)
        print("Graph image saved as andorgraph.svg")

    # useful to find shortes paths
    def find_path(self, from_node_id, to_node_id):
        queue = deque()
        queue.append(self.nodes[from_node_id])
        visited = set()
        
        parent = [None] * len(self.nodes)
        print(f'{self.nodes[from_node_id]} ==> {self.nodes[to_node_id]}')
        while queue:
            node = queue.popleft()
            visited.add(node)
            for succ in node.successors:
                if succ in visited:
                    continue
                elif succ.ID == to_node_id:
                    parent[succ.ID] = node.ID
                    path = []
                    step = to_node_id
                    path_nodes = []
                    while not parent[step] is None:
                        path.append((parent[step], step))
                        path_nodes.append(step)
                        step = parent[step]
                    return path, path_nodes
                queue.append(succ)
                parent[succ.ID] = node.ID
        print(f'PATH NOT FOUND FROM {from_node_id} to {to_node_id}')
        return [], []

    # graphviz visualization to debug landmark extraction
    def dot_output_step(self, current_node=None, successors=None, visited=None, new_landmarks=None, existing_landmarks=None):
        import graphviz
        self.counter +=1
        dot = graphviz.Digraph('AndOrGraph', format='svg')
        dot.attr(rankdir='LR')
        pred_ids = {n.ID for n in self.nodes[current_node].predecessors}
        for node in self.nodes:
            if node is None:
                continue
            
            # Default node color
            color = 'lightgrey'
            if node.ID in visited:
                color = 'lightgreen'
            if node.ID in successors:
                color = 'yellow'
            if node.ID in new_landmarks:
                color = 'blue'
            #elif node.ID in existing_landmarks:
                color = 'lightblue'
            if node.ID == current_node:
                color = 'green'
            
            style = 'filled'
            if node.ID in pred_ids:
                style='dashed'
            shape = 'circle' if node.type == NodeType.OR else 'box'
            dot.node(str(node.ID), label=node.label, shape=shape, style=style, fillcolor=color)

            
        for node in self.nodes:
            if node is None or not node.successors:
                continue
            for succ in node.successors:
                dot.edge(str(node.ID), str(succ.ID))
        
        filename = f'bottomupoutputs3/graph_{self.counter}'
        dot.render(filename, cleanup=True)
        print(f"Graph image saved as {filename}.svg")

    def _and_or_test2(self, use_landmarks):
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
        M1 = AndOrGraphNode(2, NodeType.AND, content_type=ContentType.METHOD, label="M1")
        M2 = AndOrGraphNode(3, NodeType.AND, content_type=ContentType.METHOD, label="M2")
        M3 = AndOrGraphNode(4, NodeType.AND, content_type=ContentType.METHOD, label="M3")
        M4 = AndOrGraphNode(5, NodeType.AND, content_type=ContentType.METHOD, label="M4")

        A = AndOrGraphNode(6, NodeType.AND, content_type=ContentType.OPERATOR, label="oA")
        B = AndOrGraphNode(7, NodeType.AND, content_type=ContentType.OPERATOR, label="oB")
        C = AndOrGraphNode(8, NodeType.AND, content_type=ContentType.OPERATOR, label="oC")
        D = AndOrGraphNode(9, NodeType.AND, content_type=ContentType.OPERATOR, label="oD")
        E = AndOrGraphNode(10, NodeType.AND, content_type=ContentType.OPERATOR, label="oE")

        X = AndOrGraphNode(11, NodeType.OR, content_type=ContentType.FACT, label="fx")
        Y = AndOrGraphNode(12, NodeType.OR, content_type=ContentType.FACT, label="fy")
        Z = AndOrGraphNode(13, NodeType.OR, content_type=ContentType.FACT, label="fz")

        T = AndOrGraphNode(14, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, label="T")
        S = AndOrGraphNode(15, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, label="S")
        self.fact_nodes = [X, Y, Z]
        self.task_nodes = [T, S]
        self.decomposition_nodes = [M1, M2, M3, M4]
        self.operator_nodes = [A, B, C, D, E]
        self.nodes = [None] * (len(self.fact_nodes) + len(self.task_nodes) + len(self.decomposition_nodes) + len(self.operator_nodes)+2)
        for n in self.fact_nodes + self.task_nodes + self.decomposition_nodes + self.operator_nodes + [self.init_node, self.goal_node]:
            self.nodes[n.ID] = n

        if use_landmarks:
            self.add_edge(M1,S)
            self.add_edge(A,M1)
            self.add_edge(M2,S)
            self.add_edge(B,M2)
            self.add_edge(M3,T)
            self.add_edge(C,M3)
            self.add_edge(M4,T)
            self.add_edge(D,M4)
        else:
            self.add_edge(S, M1)
            self.add_edge(M1, A)
            self.add_edge(S, M2)
            self.add_edge(M2, B)
            self.add_edge(T, M3)
            self.add_edge(M3, C)
            self.add_edge(T, M4)
            self.add_edge(M4, D)

        self.add_edge(X,A)
        self.add_edge(A,Y)
        self.add_edge(X,B)
        self.add_edge(B,Z)
        self.add_edge(X,C)
        self.add_edge(C,Z)
        self.add_edge(X,D)
        self.add_edge(Y, E)
        self.add_edge(Z, E)
        
    def _and_or_test1(self, top_down):
        '''
        oA: <x,z>
        oB: <z,>
        
        m1 : T -> S
               -> oA
        
        m2 : T -> oB

        m3 : S -> oA

        '''
        A = AndOrGraphNode(0, NodeType.AND, content_type=ContentType.OPERATOR, label="oA")
        B = AndOrGraphNode(1, NodeType.AND, content_type=ContentType.OPERATOR, label="oB")

        X = AndOrGraphNode(2, NodeType.OR, content_type=ContentType.FACT, label="fx")
        Z = AndOrGraphNode(3, NodeType.OR, content_type=ContentType.FACT, label="fz")
        

        M1 = AndOrGraphNode(4, NodeType.AND, content_type=ContentType.METHOD, label="M1")
        M2 = AndOrGraphNode(5, NodeType.AND, content_type=ContentType.METHOD, label="M2")
        M3 = AndOrGraphNode(6, NodeType.AND, content_type=ContentType.METHOD, label="M3")

        T = AndOrGraphNode(7, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, label="T")
        S = AndOrGraphNode(8, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, label="S")

        if top_down:
            self.add_edge(T, M1)
            self.add_edge(T, M2)        
            self.add_edge(M1, S)
            self.add_edge(M1, B)
            self.add_edge(M2, B)
            self.add_edge(S, M3)
            self.add_edge(M3, A)
        else:
            self.add_edge(M1, T)
            self.add_edge(M2, T)        
            self.add_edge(S, M1)
            self.add_edge(B, M1)
            self.add_edge(B, M2)
            self.add_edge(M3, S)
            self.add_edge(A, M3)
            
        
        self.add_edge(X, A)
        self.add_edge(Z, B)
        self.add_edge(A, Z)
        
        self.fact_nodes = [X, Z]
        self.task_nodes = [T, S]
        self.decomposition_nodes = [M1, M2, M3]
        self.operator_nodes = [A, B]
        
        self.nodes = [None] * (len(self.fact_nodes) + len(self.task_nodes) + len(self.decomposition_nodes) + len(self.operator_nodes))
        for n in self.fact_nodes + self.task_nodes + self.decomposition_nodes + self.operator_nodes:
            self.nodes[n.ID] = n
        
        self.i_node_set.add(X.ID)
        self.i_node_set.add(T.ID)
        if top_down:
            for i_node in self.i_node_set:
                node = self.nodes[i_node]
                print(f'node {node} removing:')
                for pred in node.predecessors:
                    print(f'edge({pred.label, node.label})')
                    self.remove_edge(pred, node)
        print(f'built andor test 1')
        
        
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
    
    

        
