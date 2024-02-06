#! /usr/bin/env python3
#
# This file is part of pyperplan.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

# TODO: Give searches and heuristics commandline options and reenable preferred
# operators.

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

def main():
    

    # Commandline parsing
    log_levels = ["debug", "info", "warning", "error"]

    # get pretty print names for the search algorithms:
    # use the function/class name and strip off '_search'
    def get_callable_names(callables, omit_string):
        names = [c.__name__ for c in callables]
        names = [n.replace(omit_string, "").replace("_", " ") for n in names]
        return ", ".join(names)

    search_names = get_callable_names(SEARCHES.values(), "_search")
    heuristic_names = get_callable_names(HEURISTICS.values(), "Heuristic")
    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    argparser.add_argument(dest="domain", nargs="?")
    argparser.add_argument(dest="problem")
    argparser.add_argument("-l", "--loglevel", choices=log_levels, default="info")
    argparser.add_argument(
        "-s",
        "--search",
        choices=SEARCHES.keys(),
        help=f"Select a search algorithm from {search_names}",
        default="blind",
    )
    argparser.add_argument(
        "-mh",
        choices=HEURISTICS.keys(),
        help=f"Select a heuristic from {heuristic_names}",
        default="blind",
    )
    args = argparser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.loglevel.upper()),
        format="%(asctime)s %(levelname)-8s %(message)s",
        stream=sys.stdout,
    )

    args.problem = os.path.abspath(args.problem)
    args.domain = os.path.abspath(args.domain)

    search = SEARCHES[args.search]
    logging.info("using search: %s" % search.__name__)
    print(search)
    heuristic = HEURISTICS[args.mh]
    logging.info("using heuristic: %s" % heuristic.__name__)
    
    #run_benchmarks()

    search_plan(
        args.domain,
        args.problem,
        search,
        heuristic
    )
    

if __name__ == "__main__":
    main()
