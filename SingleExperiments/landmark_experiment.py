import logging
from pyperplan.grounder.panda_ground import pandaGrounder
from pyperplan.tools import parse_heuristic_params
from pyperplan.search.htn_node import AstarNode
import pyperplan.FLAGS as FLAGS
def run_experiment(domain_file, problem_file, heuristic, h_params, grounder):
    grounder = pandaGrounder(domain_file, problem_file)
    grounder_status = 'SUCCESS'
    model = grounder.groundify()
    if grounder_status != 'SUCCESS':
        logging.error('Grounder failed')
    
    FLAGS.MONITOR_LM_TIME=True
    node = AstarNode(None, None, None, model.initial_state, model.initial_tn, 0, 0)
    landmark_heuristic  = heuristic(model, node, **(parse_heuristic_params(h_params)))
    print(landmark_heuristic.__output__())

    
        


    
    

