from enum import Enum
class LogicalOperator(Enum):
    NOOP = 0
    AND = 1
    OR = 2
    NOT = 3
    EQUAL = 4
    LITERAL = 5

class PriorityQueueNode:
    def __init__(self, h_value, seq_num, node):
        self.priority = seq_num
        self.h_value = h_value
        self.node = node

    def __lt__(self, other):
        return self.h_value + self.priority >  other.h_value + other.priority