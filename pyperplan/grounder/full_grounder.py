from .grounder import Grounder
from ..model import Operator, Model, AbstractTask, Decomposition
from ..parser.hddl import Problem


class FullGrounder(Grounder):
    """Full grounder (key contribution from WenBo)

    Args:
        Grounder (_type_): _description_
    """

    def __init__(self, problem: Problem):
        super().__init__(problem)

    def groundify(self):
        return super().groundify()
