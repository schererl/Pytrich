import time
from typing import Optional, Dict, Union, List
from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.Heuristics.heuristic import Heuristic
from Pytrich.Heuristics.Novelty.novelty import NoveltyFT, NoveltyLazyFT
from Pytrich.Search.htn_node import HTNNode
from Pytrich.model import Model

class NoveltyHeuristic(Heuristic):
    """
    Novelty heuristic for HTN planning.
    Computes novelty based on different configurations and integrates it into the search process.
    """
    def __init__(self, novelty_type: str = "ft", name: str = "novelty"):
        super().__init__(name=name)
        self.novelty_type = novelty_type.lower()
        self.novelty_function = None  # Assigned during initialization
        self.preprocessing_time = 0
        self.start_time = 0
        
    def initialize(self, model: Model, initial_node: HTNNode):
        """
        Initialize the heuristic with the model and the initial node.
        """
        self.start_time = time.time()
        self.novelty_function = self._get_novelty_function()
        if not self.novelty_function:
            raise ValueError(f"Unknown novelty type: {self.novelty_type}")
        self.preprocessing_time = time.time() - self.start_time
        return super().initialize(model, self._compute_novelty(initial_node))

    def _get_novelty_function(self):
        """
        Map the novelty type string to the appropriate novelty function.
        """
        novelty_functions = {
            "ft": NoveltyFT(),
            "lazyft": NoveltyLazyFT(),
        }
        return novelty_functions.get(self.novelty_type)

    def __call__(self, parent_node: HTNNode, node: HTNNode):
        """
        Compute the novelty heuristic value for the given node.
        """
        
        novelty_value = self._compute_novelty(node)
        super().update_info(novelty_value)
        return novelty_value

    def _compute_novelty(self, node: HTNNode) -> int:
        """
        Compute the novelty for a given node using the configured novelty function.
        """
        return self.novelty_function(None, node)

    def __repr__(self):
        return f"Novelty(type={self.novelty_type})"

    def __str__(self):
        return f"Novelty(type={self.novelty_type})"

    def __output__(self):
        """
        Return a string representation of the heuristic configuration and statistics.
        """
        return (
            f"Heuristic Info:\n"
            f"\tName: {self.name}\n"
            f"\tType: {self.novelty_type}\n"
            f"\tPreprocessing Time: {getattr(self, 'preprocessing_time', 0):.2f} s\n"
        )
