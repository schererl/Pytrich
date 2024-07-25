from collections import deque
from copy import deepcopy
import gc

# store landmarks, needed when landmarks are updated for each new node
class LM_Node:
    def __init__(self, parent=None):
        if parent:
            self.lms = parent.lms
            self.mark = parent.mark
            self.number_lms = parent.number_lms
            self.achieved_lms = parent.achieved_lms
        else:
            self.lms  = 0
            self.mark = 0
            self.number_lms   = 0   # total number of lms
            self.achieved_lms = 0   # total achieved lms
            
    # mark as 'achieved' if node is a lm
    def mark_lm(self, node_id):
        if self.lms & (1 << node_id) and ~self.mark & (1 << node_id):
            self.mark |= 1 << node_id
            self.achieved_lms+=1
        
    # add new lms
    def update_lms(self, new_lms):
        for lm_id in new_lms:
            if ~self.lms & (1 << lm_id):
                self.lms |= (1 << lm_id)
                self.number_lms+=1
        
    def lm_value(self):
        return self.number_lms - self.achieved_lms
    
    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlms:      {bin(self.lms)}\n\tachieved: {bin(self.mark)}"

class FALM:
    def __init__(self, model):
        self.model=model
        self.op_labels = {}
    
    def _calculate_op_achievers(self):
        for o_a in self.model.operators:
            for eff_f in o_a.get_add_effects_bitfact():
                for o in self.model.operators:
                    for pre_f in o.get_precons_bitfact():
                
                        if o_a.name == o.name:
                            continue
                        if pre_f == eff_f:
                            #print(f"{o_a.name} is achiever of {o.name}")
                            if o_a.name in self.op_labels and o.name in self.op_labels:
                                achiever = '*' if self.op_labels[o_a.name]+1 == self.op_labels[o.name] else ''
                                if achiever == '':
                                    continue

                                print(f"{o_a.global_id}[{self.op_labels[o_a.name]}] --> {o.global_id}[{self.op_labels[o.name]}] {achiever}")
                            else:
                                print(f"NOT IN: {o_a.name} or {o.name}")
                                exit(0)
                            
                        
    def segment_operators(self):
        S = [self.model.initial_state]
        acc_O = set()
        O = []

        change=True
        it = 0
        while change:
            current_state = S[-1]
            applicable_ops = {o for o in self.model.operators if o.relaxed_applicable_bitwise(current_state)} - acc_O
            if not applicable_ops:
                break
            for o in applicable_ops:
                self.op_labels[o.name] = it
            acc_O |= applicable_ops
            O.append(applicable_ops)
            new_state = deepcopy(current_state)
            for op in applicable_ops:
                new_state = op.relaxed_apply_bitwise(new_state)
            S.append(new_state)
            
            print(f'new operations: {len(applicable_ops)}')
            print(applicable_ops)
            it+=1
        print(f'iterations {it}')

        print(self.op_labels)

        self._calculate_op_achievers()
        