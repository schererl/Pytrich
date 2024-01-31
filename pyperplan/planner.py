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

from .grounder.grounding import ground

from . import search, tools
#from .pddl.parser import Parser
from .parser.parser import Parser



SEARCHES = {
    "blind": search.blind_search
}

HEURISTICS = {
    "TaskCount": search.heuristic.TaskCountHeuristic,
    "FactCount": search.heuristic.FactCountHeuristic,
    "Blind": search.heuristic.BlindHeuristic
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


def _ground(
    problem, remove_statics_from_initial_state=True, remove_irrelevant_operators=True
):
    logging.info(f"Grounding start: {problem.name}")
    model = ground(
        problem, remove_statics_from_initial_state, remove_irrelevant_operators
    )
    logging.info(f"Grounding end: {problem.name}")
    logging.info("{} Variables created".format(len(model.facts)))
    logging.info("{} Operators created".format(len(model.operators)))
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
    problem = _parse(domain_file, problem_file)
    task = _ground(problem)
    search_start_time = time.process_time()
    solution = _search(task, search, heuristic)
    logging.info("Search time: {:.2}".format(time.process_time() - search_start_time))
    return solution


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
