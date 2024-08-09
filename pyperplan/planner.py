import logging
import re
import time

# grounding
from .grounder.full_grounder import FullGrounder
from .grounder.panda_ground import pandaGrounder
# heursitic
from .heuristics.blind_heuristic import BlindHeuristic
from .heuristics.tdg_heuristic import TaskDecompositionHeuristic
from .heuristics.lm_heuristic import LandmarkHeuristic
from .heuristics.tdglm_heuristic import TDGLmHeuristic
# search
from .search.astar_search import search as astar_search
from .search.blind_search import search as blind_search

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

def _search(model, search, heuristic, h_params):
    solution = search(model, heuristic_type=heuristic, h_params=h_params)
    return solution


def search_plan(
    domain_file, problem_file, search, heuristic, h_params, grounder
):
    """
    Parses the given input files to a specific planner task and then tries to
    find a solution using the specified  search algorithm and heuristics.

    @param domain_file      The path to a domain file
    @param problem_file     The path to a problem file in the domain given by
                            domain_file
    @param search           A callable that performs a search on the task's
                            search space
    @param heuristic_class  A class implementing the heuristic_base.Heuristic
                            interface
    @param h_params         Parameters for specific heuristic configuration
    @param grounder         Grounder type used
    """
    model=None
    if issubclass(grounder, pandaGrounder):
        grounder_instance = grounder(domain_file, problem_file)
    else:
        raise NotImplementedError("The parser and full grounding are not implemented yet.")
        #parser = Parser(domain_file, problem_file)
        #grounder_instance = grounder(parser.lifted_problem)
     
    model= grounder_instance.groundify()
    result = _search(model, search, heuristic, h_params)
    return result
