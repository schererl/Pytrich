from heuristics.heuristic import Heuristic


class LoopDetecttionHeuristic(Heuristic):
    """Heuristic that detects loops and returns infinity if a loop is detected.
    Key contribution from Fan, based on the paper:
    https://ojs.aaai.org/index.php/ICAPS/article/view/15959

    Args:
        Heuristic (_type_): _description_
    """
    def __init__(self, model, initial_node):
        self.model = model

    def compute_heuristic(self, parent_node, node):
        pass
