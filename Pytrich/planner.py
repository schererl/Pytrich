import logging
import re
import time

# grounder
from Pytrich.Grounder.panda_ground import PandaGrounder
from Pytrich.Search.htn_node import AstarNode, HTNNode
# heursitic
from .Heuristics.blind_heuristic import BlindHeuristic
from .Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from .Heuristics.lm_heuristic import LandmarkHeuristic
from .Heuristics.novelty_heuristic import NoveltyHeuristic
# search
from .Search.astar_search import search as astar_search
from .Search.blind_search import search as blind_search

SEARCHES = {
    "Blind": blind_search,
    "Astar": astar_search
}

HEURISTICS = {
    "Blind"    : BlindHeuristic,
    "LMCOUNT"  : LandmarkHeuristic,
    "TDG"      : TaskDecompositionHeuristic,
    "NOVELTY"  : NoveltyHeuristic
}

NODES = {
    "HTNNode"    : HTNNode,
    "AstarNode"  : AstarNode
}

NUMBER = re.compile(r"\d+")


def search_plan(
    domain_file, problem_file, sas_file, search, heuristic, node, h_params, s_params, n_params
):
    grounder = PandaGrounder(sas_file=sas_file, domain_file=domain_file, problem_file=problem_file)
    model = grounder()
    result = search(model, heuristic_type=heuristic, node_type=node, h_params=h_params, n_params=n_params, **s_params)
    
    return result

