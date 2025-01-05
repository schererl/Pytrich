from Pytrich.Heuristics.blind_heuristic import BlindHeuristic
from Pytrich.Heuristics.tdg_heuristic import TaskDecompositionHeuristic
from Pytrich.Heuristics.lm_heuristic import LandmarkHeuristic
from Pytrich.Heuristics.novelty_heuristic import NoveltyHeuristic
from Pytrich.Heuristics.hmax_heuristic import HmaxHeuristic
from Pytrich.Heuristics.aggregation import Max, Tiebreaking

HEURISTICS = {
    "Blind": BlindHeuristic,
    "LMCOUNT": LandmarkHeuristic,
    "TDG": TaskDecompositionHeuristic,
    "NOVELTY": NoveltyHeuristic,
    "HMAX": HmaxHeuristic,
}

AGGREGATIONS = {
    "Max": Max,
    "Tiebreaking": Tiebreaking,
}
