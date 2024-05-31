from .heuristic import Heuristic
from ..model import Operator


class TaskDecompositionHeuristic(Heuristic):
    """TDG Heuristic Implementation. Key contribution from Zhichen Zhao
    Based on the paper:
    https://www.ijcai.org/proceedings/2017/0068.pdf
    Args:
        Heuristic (_type_): _description_
    """
    
    def __init__(self, model, initial_node):
        super().__init__(model, initial_node)

    