from Pytrich.Heuristics.lmcount_heuristic import LandmarkCountHeuristic
from Pytrich.Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from Pytrich.Search.htn_node import HTNNode
class NoveltyFT:
    def __init__(self):
        self.seen_tuples = set()
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs 
        return has novelty or not.
        """
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                for t in node.task_network:
                    if (bit_pos, t.global_id) not in self.seen_tuples:
                        novelty = 0
                        self.seen_tuples.add((bit_pos, t.global_id))
        
        return novelty

class NoveltyLazyFT:
    def __init__(self):
        self.seen_tuples = set()
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs considering the progressed task
        return uhas novelty or not.
        """
        if node.task is None:
            return 1
        
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((bit_pos, node.task.global_id))
        
        return novelty
    
class NoveltyH1FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.heuristic =  TaskDecompositionHeuristic(use_satis=True)
        self.initial_h = self.heuristic.initialize(model, initial_node)
        
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs considering the progressed task
        return uhas novelty or not.
        """
        h_value = self.heuristic(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos): #fato
                if (h_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h_value, bit_pos, node.task.global_id))
        
        return (novelty, h_value)
    
class NoveltyH2FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h1 =  LandmarkCountHeuristic()
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs considering the progressed task
        return uhas novelty or not.
        """
        h1_value = self.h1(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (h1_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h1_value, bit_pos, node.task.global_id))
        return (novelty, h1_value)

class NoveltyH3FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h2 =  TaskDecompositionHeuristic(use_satis=True)
        self.initial_h2 = self.h2.initialize(model, initial_node)
        self.h1 =  LandmarkCountHeuristic()
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs considering the progressed task
        return uhas novelty or not.
        """
        h1_value = self.h1(parent_node, node)
        h2_value = self.h2(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (h1_value, h2_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h1_value, h2_value, bit_pos, node.task.global_id))
        return (novelty, h1_value, h2_value)
    
class NoveltyH4FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h2 =  TaskDecompositionHeuristic(use_satis=True)
        self.initial_h2 = self.h2.initialize(model, initial_node)
        self.h1 =  LandmarkCountHeuristic()
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs considering the progressed task
        return uhas novelty or not.
        """
        h1_value = self.h1(parent_node, node)
        h2_value = self.h2(parent_node, node)
        return (h1_value, h2_value)
    
class NoveltyH5FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h1 =  TaskDecompositionHeuristic(use_satis=True)
        self.h2 =  LandmarkCountHeuristic(use_bid=True)
        self.initial_h1 = self.h1.initialize(model, initial_node)
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        h1_value = self.h1(parent_node, node)
        h2_value = self.h2(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (h1_value, h2_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h1_value, h2_value, bit_pos, node.task.global_id))
        return (novelty, h1_value, h2_value)

class NoveltyH6FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h1 =  LandmarkCountHeuristic(use_bid=True)
        self.h2 =  TaskDecompositionHeuristic(use_satis=True)
        self.initial_h1 = self.h1.initialize(model, initial_node)
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        h1_value = self.h1(parent_node, node)
        h2_value = self.h2(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (h1_value, h2_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h1_value, h2_value, bit_pos, node.task.global_id))
        return (novelty, h1_value, h2_value)
    
class NoveltyH7FT:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.h1 =  LandmarkCountHeuristic()
        self.h2 =  TaskDecompositionHeuristic(use_satis=True)
        self.initial_h1 = self.h1.initialize(model, initial_node)
        self.initial_h1 = self.h1.initialize(model, initial_node)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        h1_value = self.h1(parent_node, node)
        h2_value = self.h2(parent_node, node)
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (h1_value, bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((h1_value, bit_pos, node.task.global_id))
        return (novelty, h1_value, h2_value)