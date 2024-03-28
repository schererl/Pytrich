from enum import Enum, auto
from collections import deque, defaultdict
from ...model import Operator, Decomposition

class NodeType(Enum):
    AND = auto()
    OR = auto()


class AndOrGraphNode:
    def __init__(self, node_type, weight=0, label=''):
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
    fact_nodes=[]
    operator_nodes=[]
    decomposition_nodes = []
    task_nodes = []
    count=0
    init_node = None
    goal_node = None
    init_tn   = []

    task_id_nodes = {}
    op_id_nodes   = {}
    def __init__(self, model):
        self.init_node  = AndOrGraphNode(NodeType.AND, label='INIT')
        self.goal_node  = AndOrGraphNode(NodeType.AND, label='GOAL')
        
        number_facts = len(model.facts)
        self.fact_nodes=[None]*number_facts
        # set facts
        for fact_pos in range(number_facts):
            fact_node = AndOrGraphNode(NodeType.OR, label=model._int_to_explicit[fact_pos])
            self.fact_nodes[fact_pos] = fact_node
            
            # set initial and goal nodes
            if model.initial_state & (1 << fact_pos):
                self.add_edge(self.init_node, fact_node)
                
            if model.goals & (1 << fact_pos):
                self.add_edge(fact_node, self.goal_node)
                
        
        # set task and methods
        for t_id, t in enumerate(model.abstract_tasks):
            task_node = AndOrGraphNode(NodeType.OR, weight=1, label='task: '+t.name)
            self.task_nodes.append(task_node)
            self.task_id_nodes[t]=t_id
            
        # set intial task network
        print(model.initial_tn)
        for init_t in model.initial_tn:
            task_id = self.task_id_nodes[init_t]
            print(self.task_nodes[task_id])
            self.add_edge(self.init_node, self.task_nodes[task_id])

        self.plot_graph()


        # set operators
        for id_op, op in enumerate(model.operators):    
            operator_node = AndOrGraphNode(NodeType.AND, weight=1, label='op: '+op.name)
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
            decomposition_node = AndOrGraphNode(NodeType.AND, label='decomp: '+d.name)
            self.decomposition_nodes.append(decomposition_node)
            c_task_id = self.task_id_nodes[d.compound_task]
            self.add_edge(self.task_nodes[c_task_id], decomposition_node)
            
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
                    subt_node = self.task_nodes[self.task_id_nodes[d.compound_task]]
                self.add_edge(decomposition_node, subt_node)
        self.plot_initgraph()
        #exit()
                
    def add_edge(self, nodeA, nodeB):
        nodeA.successor.append(nodeB)
        nodeB.predecessor.append(nodeA)

    def check_rechability(self):
        process_queue = deque()
        self.init_node.forced_true=True
        process_queue.append(self.init_node)
        i = 0
        ok=True
        self.plot_initgraph(output_count=str(i))
        while process_queue:
            if i >= 20:
                exit()
            node = process_queue.popleft()
            print(node)
            for succ_node in node.successor:
                if ok:
                    self.plot_filtered_graph(output_count=str(i))
                ok=False
                print(f'\t{succ_node}')
                if succ_node.forced_true:
                    continue
                succ_node.num_forced_predecessor+=1
                if succ_node.type is NodeType.OR:
                    succ_node.forced_true=True
                    process_queue.append(succ_node)
                    i+=1
                    ok=True
                elif succ_node.num_forced_predecessor == len(succ_node.predecessor):
                    succ_node.forced_true=True
                    process_queue.append(succ_node)
                    i+=1
                    ok=True

                
                if succ_node.forced_true and succ_node == self.goal_node:
                    return 0
        
        return 100000000
                
    def update_init(self, current_state, current_task_network):
        self.plot_initgraph(output_count=str('A')+str(self.count))
        
        for succ in self.init_node.successor:
            succ.predecessor.remove(self.init_node)
        
        self.init_node.successor = []
        
        self.plot_initgraph(output_count=str('B')+str(self.count))
        self.count+=1

        for fact_pos in range(len(self.fact_nodes)):
            if current_state & (1 << fact_pos):
                fact_node = self.fact_nodes[fact_pos]
                self.add_edge(self.init_node, fact_node)
                
        for t in current_task_network:
            task_node=None
            if type(t) is Operator:
                task_node = self.operator_nodes[self.op_id_nodes[t]]
            else:
                task_node = self.task_nodes[self.task_id_nodes[t]]
            self.add_edge(self.init_node, task_node)
            
    def clear(self):
        self.goal_node.forced_true=False
        self.init_node.forced_true=False
        for n_f in self.fact_nodes:
            n_f.forced_true=False
        for n_op in self.operator_nodes:
            n_op.forced_true=False
        for n_d in self.decomposition_nodes:
            n_d.forced_true=False
        for n_t in self.task_nodes:
            n_t.forced_true=False

    def testGraph(self):
        for ch in self.init_node.successor:
            print(f'init: {ch}')
            for pred_ch in ch.successor:
                print(f'\tprecondition of {pred_ch}')
        for ch in self.goal_node.predecessor:
            print(f'goal fact: {ch}')
            
    def plot_graph(self, output_count=''):
        from graphviz import Digraph
        dot = Digraph()

        # Iterate through all nodes to add them to the graph
        all_nodes = [self.init_node, self.goal_node] + self.fact_nodes + self.task_nodes  + self.decomposition_nodes + self.operator_nodes
        for node in all_nodes:
            shape = 'circle' if node.type == NodeType.OR else 'square'
            fillcolor = 'lightgreen' if node.forced_true else 'pink'  # Correct color for non-forced nodes
            # Check if the node is either the init or goal node
            if node in [self.init_node, self.goal_node]:
                # Make init and goal nodes larger
                dot.node(str(id(node)), f"{node.label}", shape=shape, style='filled', fillcolor=fillcolor, width='1.5', height='1.5')
            else:
                dot.node(str(id(node)), f"{node.label}", shape=shape, style='filled', fillcolor=fillcolor)

        # Add edges based on successor relationships
        for node in all_nodes:
            for succ in node.successor:
                if not succ in all_nodes:
                    continue
                dot.edge(str(id(node)), str(id(succ)))

        # Specify the output format as SVG
        dot.render('./andorgraph_output/graph'+output_count, format='svg', cleanup=True)

    def plot_initgraph(self, output_count=''):
        from graphviz import Digraph
        dot = Digraph()

        # Iterate through all nodes to add them to the graph
        all_nodes = [self.init_node] + self.init_node.successor
        for node in all_nodes:
            shape = 'circle' if node.type == NodeType.OR else 'square'
            fillcolor = 'lightgreen' if node.forced_true else 'pink'  # Correct color for non-forced nodes
            # Check if the node is either the init or goal node
            if node in [self.init_node, self.goal_node]:
                # Make init and goal nodes larger
                dot.node(str(id(node)), f"{node.label}", shape=shape, style='filled', fillcolor=fillcolor, width='1.5', height='1.5')
            else:
                dot.node(str(id(node)), f"{node.label}", shape=shape, style='filled', fillcolor=fillcolor)

        # Add edges based on successor relationships
        for node in all_nodes:
            for succ in node.successor:
                if not succ in all_nodes:
                    continue
                dot.edge(str(id(node)), str(id(succ)))

        # Specify the output format as SVG
        dot.render('./andorgraph_output/initgraph'+output_count, format='svg', cleanup=True)



    def plot_filtered_graph(self, output_count=''):
        from graphviz import Digraph
        dot = Digraph()

        # Collect all nodes that are forced true
        forced_true_nodes = [node for node in [self.goal_node, self.init_node] + self.fact_nodes + self.task_nodes + self.operator_nodes + self.decomposition_nodes if node.forced_true]

        # Initialize a set to keep track of nodes already added to the graph
        added_nodes = set()
        added_edges = set()
        # For each forced true node, add it and its direct successors to the graph
        for node in forced_true_nodes:
            shape = 'circle' if node.type == NodeType.OR else 'square'
            node_id = str(id(node))
            if node_id not in added_nodes:
                dot.node(node_id, f"{node.label}", shape=shape, style='filled', fillcolor='lightgreen')
                added_nodes.add(node_id)
            
            # Add direct successors of the forced true node
            for succ in node.successor:
                if "op:" in succ.label:
                    continue
                succ_shape = 'circle' if succ.type == NodeType.OR else 'square'
                succ_color = 'lightgreen' if succ.forced_true else 'pink'
                succ_id = str(id(succ))
                if succ_id not in added_nodes:
                    dot.node(succ_id, f"{succ.label}", shape=succ_shape, style='filled', fillcolor=succ_color)
                    added_nodes.add(succ_id)
                    
                if (not (node_id, succ_id) in added_edges):
                    added_edges.add((node_id, succ_id))
                    dot.edge(node_id, succ_id)

                # Additionally, if the successor node label contains "decomp:", add its predecessors to the graph
                if "decomp:" in succ.label:
                    for pred in succ.predecessor:
                        pred_shape = 'circle' if pred.type == NodeType.OR else 'square'
                        pred_color = 'lightgreen' if pred.forced_true else 'pink'
                        pred_id = str(id(pred))
                        if pred_id not in added_nodes:
                            dot.node(pred_id, f"{pred.label}", shape=pred_shape, style='filled', fillcolor=pred_color)
                            added_nodes.add(pred_id)
                        # Ensure the edge is added only if both nodes are included in the graph
                        if pred_id in added_nodes and succ_id in added_nodes:
                            if not (pred_id, succ_id) in added_edges:
                                added_edges.add((pred_id, succ_id))
                                dot.edge(pred_id, succ_id)

        # Render the graph focusing on forced true nodes, their successors, and specifically the predecessors of nodes with "decomp:" in their labels
        dot.render(f'./andorgraph_output/graph{output_count}', format='svg', cleanup=True)






            
    
    
