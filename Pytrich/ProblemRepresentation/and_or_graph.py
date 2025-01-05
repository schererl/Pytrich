from enum import Enum, auto
from collections import deque

from Pytrich.PostProcessing.total_order_reachability import _compute_achievers_set
from Pytrich.model import Operator

class NodeType(Enum):
    AND = auto()
    OR = auto()
    INIT = auto()

class ContentType(Enum):
    OPERATOR = auto()
    ABSTRACT_TASK = auto()
    METHOD = auto()
    FACT = auto()
    ACHIEVER = auto()
    RECOMPOSITION = auto()
    Nan = auto()


class AndOrNode:
    def __init__(self, ID, LOCALID, node_type, content_type=ContentType.Nan, weight=0, str_name=''):
        self.ID = ID # node's global id
        self.LOCALID = LOCALID # component's position in model
        self.type  = node_type 
        self.content_type = content_type 
        self.successors   = []
        self.predecessors = []
        
        # specific for computing heuristic values using AND/OR structure
        self.forced_true = False
        self.num_forced_predecessors = 0
        self.weight    = weight
        self.value     = 0
        # for output
        self.str_name = str_name
        
    def __str__(self):
        return F"Node ID={self.ID}:{self.str_name}"
    def __repr__(self) -> str:
        return f"<Node {self.ID} {self.content_type}>"
    
class AndOrGraph:
    def __init__(self, model, graph_type = 0):
        self.model = model
        self.nodes = None
        self.components_count = len(model.facts) + len(model.operators) + len(model.abstract_tasks) + len(model.decompositions)
        self.init_nodes = set()
        if graph_type == 0:
            self.bu_initialize(model)
        elif graph_type == 1:
            self.td_initialize(model)
        elif graph_type == 3:
            self.tdg_initialize(model)
        elif graph_type == 4:
            self.c_initialize(model)
        else:
            print(f"Invalid Graph Type {graph_type}")
            exit(0)
        
    def tdg_initialize(self, model):
        '''
        Task Decomposition Graph only
        '''
        self.nodes = [None] * self.components_count # should ignore facts
        # set abstract task
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrNode(t.global_id, t_i, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, str_name=t.name)
            self.nodes[t.global_id]=task_node
            
        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):
            operator_node = AndOrNode(op.global_id, op_i, NodeType.AND, content_type=ContentType.OPERATOR, weight=op.cost, str_name=op.name)
            self.nodes[op.global_id] = operator_node
            
        # set methods
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrNode(d.global_id, d_i, NodeType.AND, content_type=ContentType.METHOD, str_name=d.name)
            self.nodes[d.global_id] = decomposition_node
            task_head_id = d.compound_task.global_id
            self.add_edge(decomposition_node, self.nodes[task_head_id])
            for subt in d.task_network:
                subt_node:AndOrNode = self.nodes[subt.global_id]
                self.add_edge(subt_node, decomposition_node)


    def bu_initialize(self, model):
        '''
        Bottom-up graph for computing causal landmarks:
          We refer to it as 'bottom-up' because it captures the HTN hierarchy this way
          see: Höller, D., & Bercher, P. (2021). Landmark Generation in HTN Planning. Proceedings of the AAAI Conference on Artificial Intelligence
        '''
        self.nodes = [None] * self.components_count
        # set facts
        for fact in self.model.facts:
            fact_node = AndOrNode(fact.local_id, fact.local_id, NodeType.OR, content_type=ContentType.FACT, str_name=fact.name)
            self.nodes[fact.local_id]  = fact_node
            if model.initial_state & (1 << fact.local_id):
                fact_node.type = NodeType.INIT
        
        
        # set abstract task
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrNode(t.global_id, t_i, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, str_name=t.name)
            self.nodes[t.global_id]=task_node
            
        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):
            operator_node = AndOrNode(op.global_id, op_i, NodeType.AND, content_type=ContentType.OPERATOR, str_name=op.name)
            self.nodes[op.global_id] = operator_node
            for fact_pos in range(max(op.pos_precons.bit_length(), op.add_effects.bit_length())):
                if op.pos_precons & (1 << fact_pos):
                    var_node:AndOrNode = self.nodes[fact_pos]
                    self.add_edge(var_node, operator_node)
                if op.add_effects & (1 << fact_pos):
                    var_node:AndOrNode = self.nodes[fact_pos]
                    self.add_edge(operator_node, var_node)
                    
        # set methods
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrNode(d.global_id, d_i, NodeType.AND, content_type=ContentType.METHOD, str_name=d.name)
            self.nodes[d.global_id] = decomposition_node
            task_head_id = d.compound_task.global_id
            self.add_edge(decomposition_node, self.nodes[task_head_id])
            for subt in d.task_network:
                subt_node:AndOrNode = self.nodes[subt.global_id]
                self.add_edge(subt_node, decomposition_node)
                # NOTE: removing it for know, since we are using panda grounding
                # for fact_pos in range(facts_count): 
                #     if d.pos_precons & (1 << fact_pos):
                #         fact_node = self.nodes[fact_pos]
                #         self.add_edge(fact_node, decomposition_node)

    def td_initialize(self, model):
        '''
        Top-down graph for computing causal landmarks
          Our contribution for landmark generation.
          Using this AND/OR graph encoding finds additional landmarks after exausting landmarks found by bottom-up graph.

          Encode task hierarchy using a top-down view.
        '''
        self.nodes = [None] * (self.components_count + len(model.operators))
        # set facts
        for fact in self.model.facts:
            fact_node = AndOrNode(fact.local_id, fact.local_id, NodeType.OR, content_type=ContentType.FACT, str_name=fact.name)
            self.nodes[fact.local_id]  = fact_node
            if model.initial_state & (1 << fact.local_id):
                fact_node.type = NodeType.INIT
        # set abstract task
        for t_i, t in enumerate(model.abstract_tasks):
            task_node = AndOrNode(t.global_id, t_i, NodeType.OR, content_type=ContentType.ABSTRACT_TASK, str_name=t.name)
            self.nodes[t.global_id]=task_node
        # NOTE: Recomposition Graph defines tnI as INIT node
        for task in model.initial_tn:
            self.nodes[task.global_id].type= NodeType.INIT
        # set primitive tasks -operators
        for op_i, op in enumerate(model.operators):
            operator_node = AndOrNode(op.global_id, op_i, NodeType.AND, content_type=ContentType.OPERATOR, str_name=op.name)
            recomposition_node = AndOrNode(self.components_count + op_i, op_i, NodeType.OR, content_type=ContentType.RECOMPOSITION, str_name=f'R-{op.name}')
            self.nodes[operator_node.ID] = operator_node
            self.nodes[recomposition_node.ID] = recomposition_node
            self.add_edge(recomposition_node, operator_node)
            for fact_pos in range(max(op.pos_precons.bit_length(), op.add_effects.bit_length())):
                if op.pos_precons & (1 << fact_pos):
                    var_node = self.nodes[fact_pos]
                    self.add_edge(var_node, operator_node)
                if op.add_effects & (1 << fact_pos):
                    var_node = self.nodes[fact_pos]
                    self.add_edge(operator_node, var_node)
        # set methods
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrNode(d.global_id, d_i, NodeType.AND, content_type=ContentType.METHOD, str_name=d.name)
            self.nodes[d.global_id] = decomposition_node
            task_head_id = d.compound_task.global_id
            self.add_edge(self.nodes[task_head_id], decomposition_node)
            for subt in d.task_network:
                subt_node = self.nodes[subt.global_id]
                if isinstance(subt, Operator):
                    rec_node_ID = self.components_count+subt_node.LOCALID
                    rec_node = self.nodes[rec_node_ID] # get recomposition node
                    self.add_edge(decomposition_node, rec_node) # if operator, connect decomposition to recomposition node
                else:
                    self.add_edge(decomposition_node, subt_node)
                
                # for fact_pos in range(facts_count):
                #     if d.pos_precons_bitwise & (1 << fact_pos):
                #         fact_node = self.nodes[fact_pos]
                #         self.add_edge(fact_node, decomposition_node)

    # composition graph (required to compute hmax and lmcut in DOF+TI HTN planning)
    def c_initialize(self, model):
        """
        Similar to the 'bottom-up' initialization (bu_initialize), 
        but each operator (action) is followed by a dedicated OR node
        that can connect to methods. This graph follows the direction of edges
        as in the bottom-up graph, but introduces a composition nodes for each action.
        """
        # We will add one extra OR node for each operator, so we need additional indexing.
        # Original components_count = facts + operators + abstract_tasks + decompositions
        # Now we add extra OR nodes for each operator: these will come after all existing components.
        extra_or_count = len(model.operators)  # one composition node per operator
        total_nodes_count = self.components_count + extra_or_count + 1 # goal node 
        
        self.nodes = [None] * total_nodes_count

        # 1. Set Facts (OR nodes)
        for fact in self.model.facts:
            fact_node = AndOrNode(
                fact.local_id, fact.local_id, 
                NodeType.OR, 
                content_type=ContentType.FACT, 
                str_name=fact.name
            )
            self.nodes[fact.local_id] = fact_node
            # Mark initial facts as INIT nodes
            if model.initial_state & (1 << fact.local_id):
                fact_node.type = NodeType.INIT

        # 2. Set Abstract Tasks (OR nodes)
        for t_i, t in enumerate(model.abstract_tasks):
            # Global_id of tasks and operators are unique and do not overlap with facts' IDs.
            # t.global_id should already be offset by the count of facts.
            task_node = AndOrNode(
                t.global_id, t_i, 
                NodeType.OR, 
                content_type=ContentType.ABSTRACT_TASK, 
                str_name=t.name
            )
            self.nodes[t.global_id] = task_node

        # 3. Set Primitive Tasks (Operators)
        # Operators remain AND nodes, but we now introduce a recomposition OR node for each.
        # We will create a composition OR node that follows each operator.
        offset = self.components_count  # Start indexing recomposition nodes after all original components
        for op_i, op in enumerate(model.operators):
            # op.global_id maps to the operator node
            operator_node = AndOrNode(
                op.global_id, op_i, 
                NodeType.AND, 
                content_type=ContentType.OPERATOR, 
                weight=op.cost, 
                str_name=op.name
            )
            self.nodes[op.global_id] = operator_node

            # Create composition OR node for this operator
            action_or_node_id = offset + op_i
            action_or_node = AndOrNode(
                action_or_node_id, op_i, 
                NodeType.OR, 
                content_type=ContentType.RECOMPOSITION, 
                str_name=f'R-{op.name}'
            )
            self.nodes[action_or_node_id] = action_or_node

            # Connect operator -> composition node
            self.add_edge(operator_node, action_or_node)

            # Connect facts to the operator (for preconditions) and operator to facts (for effects)
            max_bit = max(op.pos_precons.bit_length(), op.add_effects.bit_length())
            for fact_pos in range(max_bit):
                if op.pos_precons & (1 << fact_pos):
                    var_node = self.nodes[fact_pos]
                    self.add_edge(var_node, operator_node)  # fact -> operator
                if op.add_effects & (1 << fact_pos):
                    var_node = self.nodes[fact_pos]
                    self.add_edge(operator_node, var_node)  # operator -> fact

        # 4. Set Methods (Decompositions, AND nodes)
        # Methods are AND nodes that connect upward to abstract tasks and downward to their subtasks.
        # For primitive subtasks (operators), we now use their corresponding composition nodes.
        for d_i, d in enumerate(model.decompositions):
            decomposition_node = AndOrNode(
                d.global_id, d_i, 
                NodeType.AND, 
                content_type=ContentType.METHOD, 
                str_name=d.name
            )
            self.nodes[d.global_id] = decomposition_node

            # Connect method -> abstract task (as in bottom-up, method points to the abstract task)
            task_head_id = d.compound_task.global_id
            self.add_edge(decomposition_node, self.nodes[task_head_id])

            # Connect subtasks to method. If subtask is an operator, we connect from its composition node.
            for subt in d.task_network:
                subt_node = self.nodes[subt.global_id]
                if isinstance(subt, Operator):
                    # If subtask is a primitive action, connect its recomposition OR node to the method.
                    c_node_id = offset + subt_node.LOCALID
                    c_node = self.nodes[c_node_id]
                    self.add_edge(c_node, decomposition_node)
                else:
                    # If subtask is abstract, connect directly
                    self.add_edge(subt_node, decomposition_node)

        

        


    def to_initialize(self, model):
        pass
        # set total-order achievers node
        # to_achievers = _compute_achievers_set(model)
        # for o_id, achievers in to_achievers.items():
        #     if -1 in achievers:
        #         continue
            
        #     pred_lst = []
        #     use_achivers = False
        #     o = model.get_component(o_id)
        #     for fact in o.get_precons_bitfact():
        #         fn = self.nodes[fact]
        #         for p in fn.predecessors:
        #             if p.ID not in achievers: # to-achievers is less than total achievers
        #                 use_achivers=True
        #             else:
        #                 pred_lst.append(p)
        #         if use_achivers:
        #             break
        #     if use_achivers:
        #         print(f'use achivers in {o.name}')
        #         no = self.nodes[o_id]
        #         to_no = self.nodes[components_count+no.content]
        #         self.add_edge(to_no, operator_node)
        #         for p in pred_lst:
        #             print(f'\t{p.label}')
        #             to_no.predecessors.append(p)
        #             self.add_edge(p, to_no)

    def update_bu_graph(self, state):
        for fact in self.model.facts:
            fact_ao_node = self.nodes[fact.global_id]
            if fact_ao_node.type==NodeType.INIT and ~state & (1 << fact.global_id):
                fact_ao_node.type=NodeType.OR
            elif state & (1 << fact.global_id):
                fact_ao_node.type=NodeType.INIT
    
    def add_edge(self, nodeA, nodeB):
        nodeA.successors.append(nodeB)
        nodeB.predecessors.append(nodeA)
    
    def remove_edge(self, nodeA, nodeB):
        nodeA.successors.remove(nodeB)
        nodeB.predecessors.remove(nodeA)
    