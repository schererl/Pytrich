from collections import deque
from copy import deepcopy
from .and_or_graphs import AndOrGraph, NodeType  # Ensure this is correctly imported
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
        queue = deque([node for node in self.and_or_graph.fact_nodes if len(node.predecessors) == 0])
        
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
        
if __name__ == '__main__':
    graph = AndOrGraph(None, debug=True)  # Ensure correct initialization
    lm = Landmarks(graph)
    lm.generate_lms()
    for node_id, lms in enumerate(lm.landmarks):
        print(f"node{node_id} {lm.nodes[node_id]}")
        for lm_id in lms:
            print(f"\tlm {lm.nodes[lm_id]}")
