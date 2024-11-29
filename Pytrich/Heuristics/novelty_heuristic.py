# Import statements
import time
from typing import Optional, Dict, Union, List, Type

from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.Novelty.novelty import NoveltyFT, NoveltyFF, NoveltyLMcount, NoveltyLazyFT, NoveltyPairs, NoveltySumFT
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model, Operator, AbstractTask
import Pytrich.FLAGS as FLAGS

class NoveltyHeuristic(Heuristic):
    """
    Novelty heuristic for HTN planning.
    """
    def __init__(self, model: Model, initial_node: HTNNode, novelty_type: str = "ft"):
        super().__init__(model, initial_node, name=f"novelty_{novelty_type}")
        self.novelty_function = None
        self.novelty_type = novelty_type
        if novelty_type == "ft":
            self.novelty_function = NoveltyFT()
        elif novelty_type == "ff":
            self.novelty_function = NoveltyFF()
        elif novelty_type == "lazyft":
            self.novelty_function = NoveltyLazyFT()
        elif novelty_type == "sumft":
            self.novelty_function = NoveltySumFT()
        elif novelty_type == "lmcount":
            self.novelty_function = NoveltyLMcount(model, initial_node)
        elif novelty_type == "pairs":
            self.novelty_function = NoveltyPairs()
        else:
            raise ValueError(f"Unknown novelty type: {novelty_type}")

        # Compute the initial novelty
        # initial_novelty = self.novelty_function(None, initial_node)
        initial_novelty = 0
        super().set_h_f_values(initial_node, initial_novelty)
        self.initial_h = initial_node.h_value

    def __call__(self, parent_node: HTNNode, node: HTNNode):
        # Compute the novelty for the current node
        novelty_value = self.novelty_function(parent_node, node)
        super().set_h_f_values(node, novelty_value)
        return novelty_value

    

    def __output__(self):
        desc = Descriptions()
        out_str = f'Heuristic Info:\n'
        out_str += f'\t{desc("heuristic_name", self.name)}\n'
        out_str += f'\t{desc("novelty_type", self.novelty_type)}\n'
        return out_str
