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


def main():
    # Commandline parsing
    log_levels = ["debug", "info", "warning", "error"]

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
    argparser.add_argument(
        "-re", "--runExperiment", 
        choices=['tdglm', 'search', 'landmark', 'none'], default='none'
    )
    args = argparser.parse_args()

    # Basic logging setup
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()), format="%(asctime)s %(levelname)-8s %(message)s", stream=sys.stdout)
    if args.runExperiment != 'none':
        run_experiment(args.runExperiment)
    else:
        if not args.domain or not args.problem:
            argparser.error("The domain and problem arguments are required unless --runBenchmark is specified.")
        args.problem = os.path.abspath(args.problem) if args.problem else None
        args.domain  = os.path.abspath(args.domain) if args.domain else None
        search    = SEARCHES[args.search]
        heuristic = HEURISTICS[args.heuristic]
        grounder  = GROUNDERS[args.grounder]
        h_params  = args.heuristicParams # heuristic parameters
        
        logging.info('Using search: %s', search.__name__)
        logging.info('Using heuristic: %s', heuristic.__name__)
        logging.info('Using grounder: %s', grounder.__name__)

        search_plan(args.domain, args.problem, search, heuristic, h_params, grounder)

if __name__ == "__main__":
    main()
