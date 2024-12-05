import argparse
import logging
import os
import sys

from Pytrich.DESCRIPTIONS import Descriptions
from Pytrich.planner import search_plan, SEARCHES, HEURISTICS, NODES
import Pytrich.FLAGS as FLAGS
from Pytrich.tools import parse_argument_string

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
        "-en", "--experimentName",
        help="Indicate the experiment name (Optional)"
    )
    argparser.add_argument(
        "-dn", "--domainName",
        help="Indicate the domain name (Optional)"
    )
    argparser.add_argument(
        "-pn", "--problemName",
        help="Indicate the problem name (Optional)"
    )
    argparser.add_argument(
        "--sas_file", 
        help="Path to the SASplus file if the problem is already grounded."
    )
    argparser.add_argument(
        "-tor", "--totalorderreachability", 
        action="store_true",
        help="Use total-order reachability analysis during grounding post-processing"
    )
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

    argparser.add_argument(
        "-H", "--heuristic", default="TDG()",
        type=str,
        help='Specify heuristic in format "heuristic_name(param1=value1,param2=value2)"'
    )
    argparser.add_argument(
        "-S", "--search", default="Astar()",
        type=str,
        help='Specify search algorithm in format "search_name(param1=value1,param2=value2) '
            '*heuristic is not a parameter of -S, use -H to pass a heuristic with their own parameters instead*"'
    )
    argparser.add_argument(
        "-N", "--node", default="AstarNode()",
        type=str,
        help='Specify node type in format "node_type(param1=value1,param2=value2)'
    )

    # Parse the arguments
    args = argparser.parse_args()
    desc = Descriptions()
    if args.experimentName:
        print(f"{desc('experiment_name', args.experimentName)}")
    
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
    FLAGS.MONITOR_SEARCH_RESOURCES = args.monitorsearch
    FLAGS.MONITOR_LM_TIME = args.monitorlandmarks
    FLAGS.USE_TO_REACHABILITY = args.totalorderreachability

    # Extract domain and problem names if provided
    domain_name = os.path.basename(os.path.dirname(args.domain)) if args.domain else None
    problem_name = os.path.splitext(os.path.basename(args.problem))[0] if args.problem else None
    try:
        heuristic_name, heuristic_params = parse_argument_string(args.heuristic)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    try:
        search_name, search_params = parse_argument_string(args.search)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        node_name, node_params = parse_argument_string(args.node)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Configuration:")
    print(f"  Domain: {domain_name}")
    print(f"  Problem: {problem_name}")
    print(f"  Search: {search_name}, Params: {search_params}")
    print(f"  Node: {node_name}, Params: {node_params}")
    print(f"  Heuristic: {heuristic_name}, Params: {heuristic_params}")
    print()

    
    
    # Run the search plan
    result = search_plan(
        args.domain, args.problem, args.sas_file,
        SEARCHES[search_name], HEURISTICS[heuristic_name], NODES[node_name],
        heuristic_params, search_params, node_params
    )
    print("Search Result:", result)

if __name__ == "__main__":
    main()
