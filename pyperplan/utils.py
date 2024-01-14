from enum import Enum
class LogicalOperator(Enum):
    NOOP = 0
    AND = 1
    OR = 2
    NOT = 3
    EQUAL = 4
    LITERAL = 5

UNSOLVABLE = 123456789123