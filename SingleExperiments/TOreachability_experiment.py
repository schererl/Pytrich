import logging
import pyperplan.FLAGS as FLAGS
from pyperplan.grounder.panda_ground import pandaGrounder
from pyperplan.heuristics.lm_heuristic import LandmarkHeuristic
from pyperplan.heuristics.tdg_heuristic import TaskDecompositionHeuristic
from pyperplan.search.htn_node import AstarNode
from pyperplan.search.astar_search import search
from pyperplan.tools import parse_heuristic_params
def run_experiment(domain_file, problem_file, grounder):
    grounder = pandaGrounder(domain_file, problem_file)
    grounder_status = 'SUCCESS'
    model = grounder.groundify()
    if grounder_status != 'SUCCESS':
        logging.error('Grounder failed')
    FLAGS.MONITOR_LM_TIME=True
    # lm_node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    # landmark_heuristic  = LandmarkHeuristic(model, lm_node)
    # print(landmark_heuristic.__output__())
    search(model, heuristic_type=TaskDecompositionHeuristic)
    

    
        


    
    

