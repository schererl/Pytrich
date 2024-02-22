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

import importlib
import logging
import os
import re
import subprocess
import sys
import time



from . import search, tools
#from .pddl.parser import Parser
from .parser.parser import Parser



SEARCHES = {
    "blind": search.blind_search
}

HEURISTICS = {
    "TaskCount": search.heuristic.TaskCountHeuristic,
    "FactCount": search.heuristic.FactCountHeuristic,
    "Blind"    : search.heuristic.BlindHeuristic,
    "MaxCount" : search.heuristic.MaxCountHeuristic,
    "DoubleCount": search.heuristic.DoubleCountHeuristic,
    "DellEff": search.heuristic.DellEffHeuristic,
    "TaskDecomposition": search.heuristic.TaskDecompositionHeuristic
}


NUMBER = re.compile(r"\d+")


def validator_available():
    return tools.command_available(["validate", "-h"])

def _parse(domain_file, problem_file):
    # Parsing
    parser = Parser(domain_file, problem_file)
    logging.info(f"Parsing Domain {domain_file}")
    domain = parser.parse_domain()
    logging.info(f"Parsing Problem {problem_file}")
    problem = parser.parse_problem(domain)
    logging.debug(domain)
    logging.info("{} Predicates parsed".format(len(domain.predicates)))
    logging.info("{} Actions parsed".format(len(domain.actions)))
    logging.info("{} Objects parsed".format(len(problem.objects)))
    logging.info("{} Constants parsed".format(len(domain.constants)))
    return problem

from .grounder.full_grounding import FullGround
from .grounder.TDG_grounding import TDGGround
def _ground(
    problem, remove_statics_from_initial_state=True, remove_irrelevant_operators=True
):
    logging.info(f"Grounding start: {problem.name}")
    
    grounder_type = TDGGround
    #grounder_type = FullGround
    grounder = grounder_type(
        problem, remove_statics_from_initial_state, remove_irrelevant_operators
    )

    model = grounder.groundify()
    print(type(grounder))
    logging.info(f"Ground ended")
    #return grounder
    return model
    
def _search(task, search, heuristic):
    logging.info(f"Search start: {task.name}")
    solution = search(task, heuristic)
    logging.info(f"Search end: {task.name}")
    return solution


def write_solution(solution, filename):
    assert solution is not None
    with open(filename, "w") as file:
        for op in solution:
            print(op.name, file=file)


def search_plan(
    domain_file, problem_file, search, heuristic
):
    """
    Parses the given input files to a specific planner task and then tries to
    find a solution using the specified  search algorithm and heuristics.

    @param domain_file      The path to a domain file
    @param problem_file     The path to a problem file in the domain given by
                            domain_file
    @param search           A callable that performs a search on the task's
                            search space
    @param heuristic_class  A class implementing the heuristic_base.Heuristic
                            interface
    @return A list of actions that solve the problem
    """
    print(domain_file)
    print(problem_file)
    print(search)
    print(heuristic)
    problem = _parse(domain_file, problem_file)
    task = _ground(problem)
    search_start_time = time.process_time()
    result = _search(task, search, heuristic)
    search_time = time.process_time() - search_start_time
    logging.info("Search time: {:.2f} seconds".format(search_time))

    if 'solution' in result and result['solution'] is not None:
        solution_file = problem_file + ".soln"
        logging.info("Plan length: %s" % len(result['solution']))
        write_solution(result['solution'], solution_file)
        validate_solution(domain_file, problem_file, solution_file)
    else:
        logging.warning("No solution could be found")
    return result

def validate_solution(domain_file, problem_file, solution_file):
    if not validator_available():
        logging.info(
            "validate could not be found on the PATH so the plan can "
            "not be validated."
        )
        return

    cmd = ["validate", domain_file, problem_file, solution_file]
    exitcode = subprocess.call(cmd, stdout=subprocess.PIPE)

    if exitcode == 0:
        logging.info("Plan correct")
    else:
        logging.warning("Plan NOT correct")
    return exitcode == 0
