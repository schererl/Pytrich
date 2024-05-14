from .heuristic import Heuristic
from ..model import Operator, AbstractTask
from ..utils import UNSOLVABLE
from .landmarks.and_or_graphs import AndOrGraph, NodeType, ContentType
from .landmarks.sccs import SCCDetection
from .landmarks.landmark import Landmarks, LM_Node
from ..search.htn_node import AstarLMNode
from collections import deque 
import time
'''
    Use a AndOr graph to perform a reachability analysis into a htn problem.
    Check if goal node is reachable (set of facts)
'''
class LandmarkHeuristic(Heuristic):
    def __init__(self):
        super().__init__()
        self.andor_graph = None
        self.sccs = None # not working
        self.landmarks = None
        self.exit_count = 0
        self.exit_limit = 1
        
    def compute_heuristic(self, model, parent_node, node, debug=False):
        assert type(node) == AstarLMNode
        if debug:
            self.testing_landmark()
        if not parent_node:
            self.landmarks2   = Landmarks(AndOrGraph(model, top_down=True))
            self.landmarks2.top_down_lms()
            
            self.andor_graph = AndOrGraph(model, top_down=False)
            node.lm_node     = LM_Node(len(self.andor_graph.nodes))
            self.landmarks   = Landmarks(self.andor_graph)
            self.landmarks.generate_lms()

            # initialize goal fact lms
            for fact_pos in range(len(bin(model.goals))-2):
                if model.goals & (1 << fact_pos):
                    node.lm_node.update_lms(self.landmarks.landmarks[fact_pos])
            

            # mark already reached facts - 'mark_lm()' only mark facts that are indeed lms
            for fact_pos in range(min(len(bin(node.state))-2, len(bin(model.goals))-2)): 
                if node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
            
            for t in node.task_network:
                node.lm_node.update_lms(self.landmarks.landmarks[t.global_id])
            
            binary_representation = bin(node.lm_node.lms)[2:][::-1]
            for lm_id, lm_val in enumerate(binary_representation):
                if lm_val == '1':
                    andor_node = self.andor_graph.nodes[lm_id]
                    if andor_node.content_type == ContentType.OPERATOR or andor_node.content_type == ContentType.FACT:
                        #print(f'node {andor_node}\n\tadding lms {[self.andor_graph.nodes[lm] for lm in self.landmarks2.landmarks[lm_id]]}')
                        #node.lm_node.update_lms(self.landmarks2.landmarks[lm_id])
                        pass
                        
            print(f'landmarks:\n {node.lm_node}')
            binary_representation = bin(node.lm_node.lms)[2:][::-1]
            for lm_id, lm_val in enumerate(binary_representation):
                if lm_val == '1':
                    print(f'lm: {self.andor_graph.nodes[lm_id]}')

            print(f'\nSTACK b1 b2 top-down landmarks:')
            for lm_id in self.landmarks2.landmarks[39]:
                print(f'lm: {self.andor_graph.nodes[lm_id]}')
            
            print(f'\nm4_do_move_22 landmarks:')
            for lm_id in self.landmarks.landmarks[84]:
                print(f'lm: {self.andor_graph.nodes[lm_id]}')
            
            print(f'\npickmup_b1_ landmarks:')
            for lm_id in self.landmarks2.landmarks[47]:
                print(f'lm: {self.andor_graph.nodes[lm_id]}')

            
            

        else:
            node.lm_node = LM_Node(len(self.andor_graph.nodes), parent=parent_node.lm_node)
            # mark last reached task (also add decomposition here)
            node.lm_node.mark_lm(node.task.global_id)
            # in case there is a change in the state:
            if type(node.task) is Operator:
                for fact_pos in range(len(bin(node.task.add_effects_bitwise))-2):
                    if node.state & (1 << fact_pos) and ~parent_node.state & (1 << fact_pos):
                        node.lm_node.mark_lm(fact_pos)
            else: #otherwise mark the decomposition
                node.lm_node.mark_lm(node.decomposition.global_id)

        #print(node.lm_node)
        #exit()
        return node.lm_node.lm_value()
    
    #debug stuff
    def testing_landmark(self):
        self.andor_graph2 = AndOrGraph(None, top_down=True, debug=True)
        self.landmarks2   = Landmarks(self.andor_graph2)
        self.landmarks2.top_down_lms()
        
        self.andor_graph = AndOrGraph(None, top_down=False, debug=True)
        self.landmarks   = Landmarks(self.andor_graph)
        self.landmarks.generate_lms()
        
        print(f'here')
        for node in self.andor_graph.nodes:
            node_id = node.ID
            print(f'{self.andor_graph.nodes[node_id]}')
            lms = self.landmarks.landmarks[node_id]
            inv_lms = self.landmarks2.landmarks[node_id]
            for lm_id in lms:
                print(f'\tlm {self.andor_graph.nodes[lm_id]}')
            for invlm_id in inv_lms:
                print(f'\tINV lm {self.andor_graph.nodes[invlm_id]}')
        exit()




    # debug stuff
    def print_lm_pred(self, node):
        print(f'node: {self.andor_graph.nodes[node.ID]}({node.ID})')
        for lm_id in self.landmarks.landmarks[node.ID]:
            print(f'\t{self.andor_graph.nodes[lm_id]}')
            for succ in node.predecessors:
                print(f'\t\t succ {succ}')
                for lm_id in self.landmarks.landmarks[succ.ID]:
                    print(f'\t\t\t{self.andor_graph.nodes[lm_id]}')

    # def check_reachability(self):
    #     reachable_nodes = deque()
    #     reachable_nodes.append(self.andor_graph.init_node)
        
    #     while reachable_nodes:
    #         node = reachable_nodes.pop(0)
    #         if node.forced_true:
    #             continue
    #         node.forced_true=True
    #         for succ in node.successors:
    #             succ.num_forced_predecessor+=1
    #             if succ.type == NodeType.OR or (succ.type == NodeType.AND and succ.num_forced_predecessor == len(succ.predecessors)):
    #                 if succ == self.andor_graph.goal_node:
    #                     return True
    #                 reachable_nodes.append(succ)
    #     return self.check_fully_decomposable(self.andor_graph.init_node)

    # def update_init_node(self, state, task_network):
    #     for succ in self.andor_graph.init_node.successor:
    #         succ.predecessor.remove(self.init_node)

    #     self.andor_graph.init_node.successor = []
    #     for fact_pos in range(len(self.andor_graph.fact_nodes)):
    #         if state & (1 << fact_pos):
    #             fact_node = self.fact_nodes[fact_pos]
    #             self.andor_graph.add_edge(self.init_node, fact_node)

    #     for t in task_network:
    #         task_node=None
    #         if type(t) is Operator:
    #             task_node = self.andor_graph.operator_nodes[self.andor_graph.op_id_nodes[t]]
    #         else:
    #             task_node = self.andor_graph.task_nodes[self.andor_graph.task_id_nodes[t]]
    #         self.andor_graph.add_edge(self.andor_graph.init_node, task_node)

    # def clear_andor_graph(self):
    #     self.andor_graph.goal_node.forced_true=False
    #     self.andor_graph.goal_node.num_forced_predecessor=0
        
    #     self.andor_graph.init_node.forced_true=False
    #     self.andor_graph.init_node.num_forced_predecessor=0
        
    #     for n_f in self.fact_nodes:
    #         n_f.andor_graph.forced_true=False
    #         n_f.andor_graph.num_forced_predecessor=0
        
    #     for n_op in self.operator_nodes:
    #         n_op.andor_graph.forced_true=False
    #         n_op.andor_graph.num_forced_predecessor=0
        
    #     for n_d in self.decomposition_nodes:
    #         n_d.andor_graph.forced_true=False
    #         n_d.andor_graph.num_forced_predecessor=0
        
    #     for n_t in self.task_nodes:
    #         n_t.andor_graph.forced_true=False
    #         n_t.andor_graph.num_forced_predecessor=0