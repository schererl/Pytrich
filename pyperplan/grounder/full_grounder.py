from .grounder import Grounder
from ..model import Operator, Model, AbstractTask, Decomposition
from ..parser.hddl import Problem


class FullGrounder(Grounder):
    """Full grounder. 
    Key contribution from Wenbo, based on the paper:
    https://ojs.aaai.org/index.php/AAAI/article/view/6529

    Args:
        Grounder (_type_): _description_
    """

    def __init__(self, problem: Problem):
        super().__init__(problem)

    def groundify(self):
        return super().groundify()
