# store landmarks, needed when landmarks are updated for each new node
class BitLm_Node:
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
            self.achieved_lms+=1
        self.mark |= 1 << node_id
    
    # in of recomputing landmarks and update lms
    def update_lms(self, u_lms):
        #new_bits = u_lms & ~self.lms
        new_bits = u_lms & ~self.mark
        self.lms |= new_bits
        self.number_lms += new_bits.bit_count()
        
    # add new lms
    def initialize_lms(self, lms):
        # for lm_id in new_lms:
        #     if ~self.lms & (1 << lm_id):
        #         self.lms |= (1 << lm_id)
        #         self.number_lms+=1
        self.lms = lms
        self.number_lms = lms.bit_count()
    
    def lm_value(self):
        return self.number_lms - self.achieved_lms
    
    def get_unreached_landmarks(self):
        unreached = []
        for i in range(len(bin(self.lms))-2):
            if self.lms & (1 << i) and not self.mark & (1 << i):
                unreached.append(i)
        return unreached

    def __str__(self):
        return f"Lms (value={self.lm_value()}): \n\tlms: {bin(self.lms)}\n\tachieved: {bin(self.mark)}\n"