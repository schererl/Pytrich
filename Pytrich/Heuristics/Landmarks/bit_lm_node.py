# store landmarks, needed when landmarks are updated for each new node
class BitLm_Node:
    def __init__(self, parent=None):
        if parent:
            self.lms = parent.lms
            self.mark = parent.mark
            self.total_cost = parent.total_cost
            self.achieved_cost = parent.achieved_cost
        else:
            self.lms  = 0
            self.mark = 0
            self.total_cost   = 0   # total number of lms
            self.achieved_cost = 0   # total achieved lms
            
    # mark as 'achieved' if node is a lm and not already marked
    def mark_lm(self, node_id, lm_cost=1):
        if self.lms & (1 << node_id) and ~self.mark & (1 << node_id):
            self.achieved_cost+=lm_cost
        self.mark |= 1 << node_id

    def is_active_lm(self, node_id):
        return self.lms & (1 << node_id) and ~self.mark & (1 << node_id)
    
    # for recomputing landmarks and update lms
    def update_lms(self, u_lms):
        new_bits = u_lms & ~self.mark
        self.lms |= new_bits
        self.total_cost += new_bits.bit_count()
        
    # add new lms
    def initialize_lms(self, lms, lm_sum=None):
        self.total_cost = lm_sum if lm_sum else lms.bit_count()
        self.lms=lms
    
    def lm_value(self):
        return self.total_cost - self.achieved_cost
    
    def get_unreached_landmarks(self):
        unreached = []
        for i in range(len(bin(self.lms))-2):
            if self.lms & (1 << i) and not self.mark & (1 << i):
                unreached.append(i)
        return unreached

    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlms: {bin(self.lms)}\n\tachieved: {bin(self.mark)}\n"