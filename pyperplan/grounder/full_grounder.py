from .grounder import Grounder
from ..model import Operator, Model, AbstractTask, Decomposition
from ..parser.hddl import Problem

class FullGrounder(Grounder):
    def __init__(self,
        problem
    ):
        super().__init__(problem)

    def groundify(self):
        return super().groundify()


