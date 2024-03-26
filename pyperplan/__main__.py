import argparse
import logging
import os
import sys

from pyperplan.planner import (
    search_plan,
    SEARCHES,
    HEURISTICS,
    validate_solution,
    write_solution,
)

from run_benchmarks import run_benchmarks
# running example: python3 pyperplan/__main__.py -H TaskDecompositionPlus -s 'Astar' htn-benchmarks/Blocksworld-GTOHP/domain.hddl htn-benchmarks/Blocksworld-GTOHP/p01.hddl  ─╯

def main():
    sys.setrecursionlimit(2000)
    # Commandline parsing
    log_levels = ["debug", "info", "warning", "error"]

    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("domain", nargs="?", help="Path to the domain file. Optional if running benchmarks.")
    argparser.add_argument("problem", nargs="?", help="Path to the problem file. Required unless running benchmarks.")
    argparser.add_argument("-l", "--loglevel", choices=log_levels, default="info")
    argparser.add_argument("-s", "--search", choices=SEARCHES.keys(), default="Blind")
    argparser.add_argument("-H", "--heuristic", choices=HEURISTICS.keys(), default="Blind")
    argparser.add_argument("-rb", "--runBenchmark", action='store_true', help="Flag to run benchmarks. If set, domain and problem arguments are ignored.")
    argparser.add_argument("-po", "--pandaOpt", action='store_true', help="Use the pandaGrounder for parsing an already grounded problem.")
    args = argparser.parse_args()

    # Basic logging setup
    logging.basicConfig(level=getattr(logging, args.loglevel.upper()), format="%(asctime)s %(levelname)-8s %(message)s", stream=sys.stdout)

    if args.runBenchmark:
        run_benchmarks(pandaOpt=args.pandaOpt)
    else:
        if not args.domain or not args.problem:
            argparser.error("The domain and problem arguments are required unless --runBenchmark is specified.")
        
        args.problem = os.path.abspath(args.problem) if args.problem else None
        args.domain = os.path.abspath(args.domain) if args.domain else None

        search = SEARCHES[args.search]
        heuristic = HEURISTICS[args.heuristic]
        logging.info(f"Using search: {search.__name__}")
        logging.info(f"Using heuristic: {heuristic.__name__}")

        search_plan(args.domain, args.problem, search, heuristic, pandaOpt=args.pandaOpt)

if __name__ == "__main__":
    main()
