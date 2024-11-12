import argparse
import logging
import os
import sys

from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.planner import search_plan, SEARCHES, HEURISTICS
import Pytrich.FLAGS as FLAGS

def main():
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(
        "domain", nargs="?", 
        help="Path to the domain file (required if --sas_file is not provided)."
    )
    argparser.add_argument(
        "problem", nargs="?", 
        help="Path to the problem file (required if --sas_file is not provided)."
    )
    argparser.add_argument(
        "--sas_file", 
        help="Path to the SASplus file if the problem is already grounded."
    )
    argparser.add_argument(
        "-s", "--search", 
        choices=SEARCHES.keys(), default="Astar",
        help="Search strategy to use."
    )
    argparser.add_argument(
        "-H", "--heuristic", 
        choices=HEURISTICS.keys(), default="TDG",
        help="Heuristic to use."
    )
    argparser.add_argument(
        "-hp", "--heuristicParams",
        help="Comma-separated list of heuristic parameters in the format key1=value1,key2=value2"
    )
    argparser.add_argument(
        "-sp", "--searchParams",
        help="Comma-separated list of scalar values for search parameters, e.g., 'g=0,h=1' for GBFS"
    )
    argparser.add_argument(
        "-tor", "--totalorderreachability", 
        action="store_true",
        help="Use total-order reachability analysis during grounding post-processing"
    )

    # Logging options
    argparser.add_argument(
        "-mg", "--monitorgrounder", 
        action="store_true",
        help="If set, enables monitoring grounding"
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

    args = argparser.parse_args()

    # Check for exclusive usage of sas_file or domain and problem
    if args.sas_file:
        if args.domain or args.problem:
            argparser.error("Cannot specify both --sas_file and domain/problem. Choose one.")
        if not os.path.isfile(args.sas_file):
            argparser.error(f"SAS file '{args.sas_file}' does not exist.")
    else:
        if not args.domain or not args.problem:
            argparser.error("Both domain and problem files must be specified if --sas_file is not provided.")
        if not os.path.isfile(args.domain):
            argparser.error(f"Domain file '{args.domain}' does not exist.")
        if not os.path.isfile(args.problem):
            argparser.error(f"Problem file '{args.problem}' does not exist.")

    # Assign flags
    FLAGS.LOG_GROUNDER = args.loggrounder
    FLAGS.LOG_SEARCH = args.logsearch
    FLAGS.LOG_HEURISTIC = args.logheuristic
    FLAGS.MONITOR_SEARCH_RESOURCES = args.monitorsearch
    FLAGS.MONITOR_LM_TIME = args.monitorlandmarks
    FLAGS.USE_TO_REACHABILITY = args.totalorderreachability

    # Extract domain and problem names if provided
    domain_name = os.path.basename(args.domain) if args.domain else None
    problem_name = os.path.splitext(os.path.basename(args.problem))[0] if args.problem else None

    descriptions = Descriptions()
    if domain_name:
        print(f'{descriptions("domain", domain_name)}')
    if problem_name:
        print(f'{descriptions("problem", problem_name)}')

    # Run the search plan
    result = search_plan(args.domain, args.problem, args.sas_file, SEARCHES[args.search], HEURISTICS[args.heuristic], args.heuristicParams, args.searchParams)
    print("Search Result:", result)

if __name__ == "__main__":
    main()
