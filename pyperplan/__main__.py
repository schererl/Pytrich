import argparse
import logging
import os
import sys
from Experiments.run_experiment import run_experiment
from pyperplan.planner import (
    search_plan,
    SEARCHES,
    HEURISTICS,
    GROUNDERS
)

import pyperplan.FLAGS as FLAGS
import SingleExperiments.landmark_experiment as lge
import SingleExperiments.TOreachability_experiment as tore

def main():
    # Commandline parsing
    log_levels = ["debug", "info", "warning", "error", "critical"]

    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(
        "domain", nargs="?", 
        help="Path to the domain file. Optional if running benchmarks."
    )
    argparser.add_argument(
        "problem", nargs="?", 
        help="Path to the problem file. Required unless running benchmarks."
    )
    argparser.add_argument(
        "-l", "--loglevel", 
        choices=log_levels, default="info"
    )
    argparser.add_argument(
        "-s", "--search", 
        choices=SEARCHES.keys(), default="Astar"
    )
    argparser.add_argument(
        "-H", "--heuristic", 
        choices=HEURISTICS.keys(), default="Blind"
    )
    argparser.add_argument(
        "-hp", "--heuristicParams",
        help="Comma-separated list of heuristic parameters in the format key1=value1,key2=value2"
    )
    argparser.add_argument(
        "-g", "--grounder",
        choices=GROUNDERS.keys(), default="panda", help="Grounder to use"
    )

    # Define mutually exclusive group for experiments
    experiment_group = argparser.add_mutually_exclusive_group()
    experiment_group.add_argument(
        "-re", "--runExperiment", 
        choices=['tdglm', 'search', 'landmark', 'none'], default='none'
    )
    
    experiment_group.add_argument(
        "-lge", "--landmarkGenerationExperiment", 
        action="store_true", 
        help="Run landmark generation experiment"
    )

    experiment_group.add_argument(
        "-tore", "--TOReachabilityExperiment", 
        action="store_true", 
        help="Run Total-Order reachability experiment"
    )

    argparser.add_argument(
        "-lg", "--loggrounder", 
        action="store_true", 
        help="If set, enables logging for the grounder"
    )
    argparser.add_argument(
        "-ns", "--nologsearch", 
        action="store_false", 
        dest="logsearch",
        help="If set, disables logging for the search"
    )
    argparser.add_argument(
        "-nh", "--nologheuristic", 
        action="store_false", 
        dest="logheuristic",
        help="If set, disables logging for the heuristic"
    )
    argparser.add_argument(
        "-ms", "--monitorsearch", 
        action="store_true", 
        help="If set, enables monitoring of resources (time and memory) during searching"
    )
    argparser.add_argument(
        "-ml", "--monitorlandmarks", 
        action="store_true", 
        help="If set, enables monitoring time during landmark generation"
    )

    argparser.add_argument(
        "-tor", "--totalorderreachability", 
        action="store_true", 
        help="Use total-order reachability analysis during grounding post-processing"
    )

    args = argparser.parse_args()

    FLAGS.LOG_GROUNDER = args.loggrounder
    FLAGS.LOG_SEARCH = args.logsearch  
    FLAGS.LOG_HEURISTIC = args.logheuristic  
    FLAGS.MONITOR_SEARCH_RESOURCES = args.monitorsearch
    FLAGS.MONITOR_LM_TIME = args.monitorlandmarks
    FLAGS.USE_TO_REACHABILITY = args.totalorderreachability

    domain_name = os.path.basename(os.path.dirname(os.path.abspath(args.domain)))
    problem_name = os.path.splitext(os.path.basename(args.problem))[0]

    # Basic logging setup
    logging.basicConfig(
        level=getattr(logging, args.loglevel.upper(), logging.INFO), 
        format="%(asctime)s %(levelname)-8s %(message)s", 
        stream=sys.stdout
    )
    if args.runExperiment != 'none':
        run_experiment(args.runExperiment)
    else:
        if not args.domain or not args.problem:
            argparser.error("The domain and problem arguments are required unless --runBenchmark is specified.")
            
        print(f'Domain: {domain_name}')
        print(f'Problem: {problem_name}')
        args.problem = os.path.abspath(args.problem) if args.problem else None
        args.domain  = os.path.abspath(args.domain) if args.domain else None

        if args.landmarkGenerationExperiment:
            heuristic    = HEURISTICS["LMCOUNT"]
            grounder     = GROUNDERS[args.grounder]
            h_params     = args.heuristicParams
            lge.run_experiment(args.domain, args.problem, heuristic, h_params, grounder)
        elif args.TOReachabilityExperiment:
            grounder     = GROUNDERS[args.grounder]
            h_params     = args.heuristicParams
            lge.run_experiment(args.domain, args.problem, grounder)
        else:
            search       = SEARCHES[args.search]
            heuristic    = HEURISTICS[args.heuristic]
            grounder     = GROUNDERS[args.grounder]
            h_params     = args.heuristicParams # heuristic parameters
            search_plan(args.domain, args.problem, search, heuristic, h_params, grounder)

if __name__ == "__main__":
    main()
