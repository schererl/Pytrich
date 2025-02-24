from copy import deepcopy


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
        new_lms = []
        for lm in self.lms:
            if node_id not in lm:
                new_lms.append(lm)
        self.achieved_lms = self.number_lms - len(new_lms)
        self.lms = new_lms

    def initialize_lms(self, lms):
        self.lms = lms
        self.number_lms = len(lms)
        self.achieved_lms = 0

    def lm_value(self):
        return self.number_lms - self.achieved_lms

    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlandmarks: {self.lms}\n\tachieved: {self.achieved_lms}"
