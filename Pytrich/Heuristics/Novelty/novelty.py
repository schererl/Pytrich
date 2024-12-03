from typing import Optional, Type, Union, List, Dict

from Pytrich.Heuristics.Landmarks.landmark import LM_Node, Landmarks
from Pytrich.Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import AbstractTask, Operator


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
    
class NoveltySumFT:
    def __init__(self):
        self.seen_tuples = set()
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        Compute the novelty of a node based on unseen (fact, task) pairs 
        return the sum of unseen pairs.
        """
        novelty = 0
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                for t in node.task_network:
                    if (bit_pos, t.global_id) not in self.seen_tuples:
                        novelty +=1
                        self.seen_tuples.add((bit_pos, t.global_id))
        
        return -novelty

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
    
class NoveltyFF:
    def __init__(self):
        self.seen_tuples = set()
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        novelty = 1
        
        if isinstance(node.task,Operator):
            #bits_set = [bit_pos for bit_pos in range(node.state.bit_length()) if node.state & (1 << bit_pos)]
            for pos_add in range(node.task.add_effects.bit_length()):
                if ~node.task.add_effects & (1 << pos_add):
                    continue
                for pos_s in range(node.state.bit_length()):
                    if ~node.state & (1 << pos_s):
                        continue
                    pair = (min(pos_add, pos_s), max(pos_add, pos_s))
                    if pair not in self.seen_tuples:
                        self.seen_tuples.add(pair)
                        novelty=0
                    
        return novelty
    
class NoveltyPairs:
    def __init__(self):
        self.seen_tuples = set()
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        novelty = 1
        
        if isinstance(node.task,Operator):
            for pos_add in range(node.task.add_effects.bit_length()):
                if ~node.task.add_effects & (1 << pos_add):
                    continue
                for pos_s in range(node.state.bit_length()):
                    if ~node.state & (1 << pos_s):
                        continue
                    pair = (min(pos_add, pos_s), max(pos_add, pos_s))
                    if pair not in self.seen_tuples:
                        self.seen_tuples.add(pair)
                        novelty=0
        else:
            for t in node.task_network[1:]:
                pair = (node.task.global_id, t.global_id)
                if pair not in self.seen_tuples:
                    self.seen_tuples.add(pair)
                    novelty=0
                    
        return novelty
    
class NoveltyLMcount:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        
        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(model, False)
        self.landmarks.generate_bottom_up()
        self.landmarks.bottom_up_lms()
        initial_node.lm_node.initialize_lms(self.landmarks.bu_lms)
        for fact_pos in range(initial_node.state.bit_length()):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)

    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        node.lm_node.mark_lm(node.task.global_id)
        if isinstance(node.task, Operator):
            for fact_pos in range(node.task.add_effects.bit_length()):
                if node.task.add_effects & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
        else:
            node.lm_node.mark_lm(node.decomposition.global_id)
        
        novelty = 1
        
        # for bit_pos in range(node.state.bit_length()):
        #     if node.state & (1 << bit_pos):
        #         for t in node.task_network:
        #             if (bit_pos, t.global_id) not in self.seen_tuples:
        #                 novelty = 0
        #                 self.seen_tuples.add((bit_pos, t.global_id))
        
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((bit_pos, node.task.global_id))
        
        # if isinstance(node.task,Operator):
        #     for pos_add in range(node.task.add_effects.bit_length()):
        #         if ~node.task.add_effects & (1 << pos_add):
        #             continue
        #         for pos_s in range(node.state.bit_length()):
        #             if ~node.state & (1 << pos_s):
        #                 continue
        #             pair = (min(pos_add, pos_s), max(pos_add, pos_s))
        #             if pair not in self.seen_tuples:
        #                 self.seen_tuples.add(pair)
        #                 novelty=0

        if novelty==1:
            return  node.lm_node.lm_value()
        return novelty
    

class NoveltyTDG:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.tdg_heuristic = TaskDecompositionHeuristic(model, initial_node, is_satis=False)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        novelty = 1
        
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((bit_pos, node.task.global_id))
        
        if novelty==1:
            return  sum([self.tdg_heuristic.tdg_values[t.global_id] for t in node.task_network])
        return novelty
    
class NoveltySatisTDG:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        self.tdg_heuristic = TaskDecompositionHeuristic(model, initial_node, is_satis=True)
    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        novelty = 1
        
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                if (bit_pos, node.task.global_id) not in self.seen_tuples:
                    novelty = 0
                    self.seen_tuples.add((bit_pos, node.task.global_id))
        
        if novelty==1:
            return  sum([self.tdg_heuristic.tdg_values[t.global_id] for t in node.task_network])
        return novelty

class NoveltyHFT1:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        
        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(model, False)
        self.landmarks.generate_bottom_up()
        self.landmarks.bottom_up_lms()
        initial_node.lm_node.initialize_lms(self.landmarks.bu_lms)
        for fact_pos in range(initial_node.state.bit_length()):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)

    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        node.lm_node.mark_lm(node.task.global_id)
        if isinstance(node.task, Operator):
            for fact_pos in range(node.task.add_effects.bit_length()):
                if node.task.add_effects & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
        else:
            node.lm_node.mark_lm(node.decomposition.global_id)
        
        novelty = 1
        
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                for t in node.task_network:
                    if (node.lm_node.lm_value(), bit_pos, t.global_id) not in self.seen_tuples:
                        novelty = 0
                        self.seen_tuples.add((node.lm_node.lm_value(), bit_pos, t.global_id))
        
        return novelty
    
class NoveltyHFT2:
    def __init__(self, model, initial_node):
        self.seen_tuples = set()
        
        initial_node.lm_node = LM_Node()
        self.landmarks = Landmarks(model, False)
        self.landmarks.generate_bottom_up()
        self.landmarks.bottom_up_lms()
        initial_node.lm_node.initialize_lms(self.landmarks.bu_lms)
        for fact_pos in range(initial_node.state.bit_length()):
            if initial_node.state & (1 << fact_pos):
                initial_node.lm_node.mark_lm(fact_pos)

    def __call__(self, parent_node:HTNNode, node:HTNNode) -> int:
        """
        
        """
        node.lm_node = LM_Node(parent=parent_node.lm_node)
        node.lm_node.mark_lm(node.task.global_id)
        if isinstance(node.task, Operator):
            for fact_pos in range(node.task.add_effects.bit_length()):
                if node.task.add_effects & (1 << fact_pos) and node.state & (1 << fact_pos):
                    node.lm_node.mark_lm(fact_pos)
        else:
            node.lm_node.mark_lm(node.decomposition.global_id)
        
        novelty = 1
        for bit_pos in range(node.state.bit_length()):
            if node.state & (1 << bit_pos):
                for t in node.task_network:
                    if (node.lm_node.lm_value(), bit_pos, t.global_id) not in self.seen_tuples:
                        novelty = 0
                        self.seen_tuples.add((node.lm_node.lm_value(), bit_pos, t.global_id))
        
        if novelty==1:
            return  node.lm_node.lm_value()
        return novelty