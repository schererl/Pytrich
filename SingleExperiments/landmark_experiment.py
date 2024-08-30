import logging
from Pyperplan.Grounder.panda_ground import pandaGrounder
from Pyperplan.tools import parse_search_params
from Pyperplan.Search.htn_node import AstarNode
import Pyperplan.FLAGS as FLAGS
def run_experiment(domain_file, problem_file, heuristic, h_params, grounder):
    grounder = pandaGrounder(domain_file, problem_file)
    grounder_status = 'SUCCESS'
    model = grounder.groundify()
    if grounder_status != 'SUCCESS':
        logging.error('Grounder failed')
    
    FLAGS.MONITOR_LM_TIME=True
    node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    landmark_heuristic  = heuristic(model, node, **(parse_search_params(h_params)))
    print(landmark_heuristic.__output__())