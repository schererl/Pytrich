from copy import deepcopy


###############################################################################
# LMC_Node: Storage for disjunctive landmarks in a search node
###############################################################################
class LMC_Node:
    def __init__(self, parent=None):
        if parent:
            self.lms = deepcopy(parent.lms)
            self.number_lms = parent.number_lms
            self.achieved_lms = parent.achieved_lms
        else:
            self.lms = set()
            self.number_lms = 0
            self.achieved_lms = 0

    def mark_lm(self, node_id):
        """
        Mark as 'achieved' any disjunctive landmark for which node_id appears.
        (If a landmark is a disjunction, achieving any one alternative satisfies it.)
        """
        # We remove any landmark (disjunctive set) that contains node_id.
        new_lms = set()
        for lm in self.lms:
            if node_id not in lm:
                new_lms.add(lm)
        # Update achieved count as the difference between the original count and the ones left.
        self.achieved_lms = self.number_lms - len(new_lms)
        self.lms = new_lms

    def initialize_lms(self, lms):
        """
        Initialize the node’s landmark structure.
        Parameter:
          lms -- a set of landmarks, where each landmark is represented as a frozenset
                 of integer IDs (e.g. {3} or {4, 7} for disjunctions)
        """
        self.lms = lms
        self.number_lms = len(lms)
        self.achieved_lms = 0

    def lm_value(self):
        """
        Returns a simple measure: the number of remaining (unachieved) landmarks.
        """
        return self.number_lms - self.achieved_lms

    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlandmarks: {self.lms}\n\tachieved: {self.achieved_lms}"
