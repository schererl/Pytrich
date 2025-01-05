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