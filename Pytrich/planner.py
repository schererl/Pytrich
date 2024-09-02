import logging
import re
import time

# grounding
from .Grounder.full_grounder import FullGrounder
from .Grounder.panda_ground import pandaGrounder
# heursitic
from .Heuristics.blind_heuristic import BlindHeuristic
from .Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from .Heuristics.lm_heuristic import LandmarkHeuristic
from .Heuristics.tdglm_heuristic import TDGLmHeuristic
# search
from .Search.astar_search import search as astar_search
from .Search.blind_search import search as blind_search

SEARCHES = {
    "Blind": blind_search,
    "Astar": astar_search
}

HEURISTICS = {
    "Blind"    : BlindHeuristic,
    "LMCOUNT": LandmarkHeuristic,
    "TDG":       TaskDecompositionHeuristic,
    "TDGLM":     TDGLmHeuristic
}

GROUNDERS = {
    "panda"    : pandaGrounder,
    "full"     : FullGrounder
}

NUMBER = re.compile(r"\d+")


def search_plan(
    domain_file, problem_file, search, heuristic, h_params, f_params, grounder
):
    model = None
    if issubclass(grounder, pandaGrounder):
        grounder_instance = grounder(domain_file, problem_file)
    else:
        raise NotImplementedError("The parser and full grounding are not implemented yet.")
     
    model = grounder_instance.groundify()
    result = search(model, heuristic_type=heuristic, h_params=h_params, f_params=f_params)
    
    return result

