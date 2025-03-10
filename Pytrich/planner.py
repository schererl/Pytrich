import logging
import re
import time

# grounder
from Pytrich.Grounder.panda_ground import PandaGrounder
from Pytrich.Heuristics.aggregation import Max, Tiebreaking
from Pytrich.Heuristics.hmax_heuristic import HmaxHeuristic
from Pytrich.Search.htn_node import AstarNode, HTNNode, TiebreakingNode
# heursitic
from .Heuristics.blind_heuristic import BlindHeuristic
from .Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from .Heuristics.lmcount_heuristic import LandmarkCountHeuristic
from .Heuristics.novelty_heuristic import NoveltyHeuristic
# search
from .Search.astar_search import search as astar_search
from .Search.blind_search import search as blind_search
from .Search.depth_first_search import search as depth_first_search
from .Search.recdepth_first_search import search as recdepth_first_search

SEARCHES = {
    "Blind": blind_search,
    "Astar": astar_search,
    "DFS": depth_first_search,
    "rDFS": recdepth_first_search,
}

HEURISTICS = {
    "Blind"    : BlindHeuristic,
    "LMCOUNT"  : LandmarkCountHeuristic,
    "TDG"      : TaskDecompositionHeuristic,
    "NOVELTY"  : NoveltyHeuristic,
    "HMAX"     : HmaxHeuristic
}

NODES = {
    "HTNNode"    : HTNNode,
    "AstarNode"  : AstarNode,
    "GreedyNode"  : AstarNode,
    "TiebreakingNode": TiebreakingNode
}

AGGREGATIONS = {
    "Max": Max,
    "Tiebreaking": Tiebreaking,
}

NUMBER = re.compile(r"\d+")


def search_plan(
    domain_file, problem_file, sas_file, heuristic_function, search, node, s_params, n_params
):
    grounder = PandaGrounder(sas_file=sas_file, domain_file=domain_file, problem_file=problem_file)
    model = grounder()
    result = search(model, heuristic=heuristic_function, node_type=node, n_params=n_params, **s_params)
    
    return result

