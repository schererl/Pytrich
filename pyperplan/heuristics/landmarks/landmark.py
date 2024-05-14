from collections import deque
from copy import deepcopy
from .and_or_graphs import AndOrGraph, NodeType, ContentType  # Ensure this is correctly imported
from .sccs import SCCDetection
# store landmarks, needed when landmarks are updated for each new node
class LM_Node:
    def __init__(self, len_nodes, parent=None):
        if parent:
            self.lms = parent.lms
            self.mark = parent.mark
            self.number_lms = parent.number_lms
            self.achieved_lms = parent.achieved_lms
        else:
            self.lms  = 0
            self.mark = 0
            self.number_lms   = 0   # total number of lms
            self.achieved_lms = 0   # total reached lms

    # mark as 'achieved' if node is a lm
    def mark_lm(self, node_id):
        if self.lms & (1 << node_id) and ~self.mark & (1 << node_id):
            self.mark |= 1 << node_id
            self.achieved_lms+=1
            
    # add new lms
    def update_lms(self, new_lms):
        for lm_id in new_lms:
            if (~self.lms & (1 << lm_id)):
                self.lms |= (1 << lm_id)
                self.number_lms+=1
            
    
    def lm_value(self):
        return self.number_lms - self.achieved_lms
    
    def __str__(self):
        lms_bin = format(self.lms, '0{}b'.format(len(str(bin(self.lms)))-2))[::-1]  # -2 to remove '0b'
        achieved_bin = format(self.mark, '0{}b'.format(len(str(bin(self.mark)))-2))[::-1]
        return f"Lms (value={self.lm_value()}): \n\t{lms_bin}\n\t{achieved_bin}"

class Landmarks:
    def __init__(self, and_or_graph):
        self.and_or_graph = and_or_graph
        self.landmarks = [set()] * len(self.and_or_graph.nodes)
        
    # generate landmarks starting ate free facts
    # stop when no landmarks can be created
    def generate_lms(self):
        queue = deque([node for node in self.and_or_graph.nodes if len(node.predecessors) == 0])
        while queue:
            node = queue.popleft()
            new_landmarks= set()
            
            if node.type == NodeType.OR and node.predecessors:
                new_landmarks = set.intersection(*(self.landmarks[pred.ID] for pred in node.predecessors))
                
            elif node.type == NodeType.AND and node.predecessors:
                new_landmarks = set.union(*(self.landmarks[pred.ID] for pred in node.predecessors))
                
            new_landmarks = new_landmarks | {node.ID}
            if  new_landmarks > self.landmarks[node.ID]:
                self.landmarks[node.ID] = new_landmarks
                for succ in node.successors:
                    if all(len(self.landmarks[pred.ID])!=None for pred in succ.predecessors):
                        queue.append(succ)

    def top_down_lms(self):
        queue = deque([self.and_or_graph.nodes[node_id] for node_id in self.and_or_graph.i_node_set])
        print(queue)
        
        dot_visited = set()
        while queue:
            node = queue.popleft()
            new_landmarks= set()
            dot_visited |= {node.ID}
            dot_successors = {succ.ID for succ in node.successors}
            dot_newlms = {}
            dot_existinglms = {}
            
            if node.content_type == ContentType.OPERATOR and node.predecessors:
                possible_method_landmarks = []
                forced_landmarks = set()
                for pred in node.predecessors:
                    if pred.content_type == ContentType.METHOD:
                        possible_method_landmarks.append(self.landmarks[pred.ID])
                    else:
                        forced_landmarks |= self.landmarks[pred.ID]
                
                if possible_method_landmarks:
                    new_landmarks = set.intersection(*(i for i in possible_method_landmarks)) 
                    
                #new_landmarks|= forced_landmarks

            elif node.type == NodeType.OR and node.predecessors:
                new_landmarks = set.intersection(*(self.landmarks[pred.ID] for pred in node.predecessors))
            elif node.type == NodeType.AND and node.predecessors:
                new_landmarks = set.union(*(self.landmarks[pred.ID] for pred in node.predecessors))
            
            new_landmarks|= {node.ID}
            
            # not sure if this terminates
            if  new_landmarks != self.landmarks[node.ID]:
                print(f'New lms: {node.label}\n\t{[self.and_or_graph.nodes[id].label for id in self.landmarks[node.ID]]}')
                dot_existinglms = self.landmarks[node.ID]
                dot_newlms = new_landmarks - self.landmarks[node.ID]
                self.landmarks[node.ID] = new_landmarks

                #if "m7_do_clear_8" in node.label or "op:stack_b1_b2" in node.label or "m5_do_move_4" in node.label or "m4_do_move_3" in node.label:
                # self.and_or_graph.dot_output_step(
                #     current_node=node.ID, 
                #     successors=dot_successors, 
                #     new_landmarks=dot_newlms, 
                #     visited= dot_visited,
                #     existing_landmarks=dot_existinglms
                # )

                for succ in node.successors:
                    if all(len(self.landmarks[pred.ID])!=None for pred in succ.predecessors):
                        queue.append(succ)
        
if __name__ == '__main__':
    graph = AndOrGraph(None, debug=True)  # Ensure correct initialization
    lm = Landmarks(graph)
    lm.generate_lms()
    for node_id, lms in enumerate(lm.landmarks):
        print(f"node{node_id} {lm.nodes[node_id]}")
        for lm_id in lms:
            print(f"\tlm {lm.nodes[lm_id]}")
