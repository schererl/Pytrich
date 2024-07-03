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
import subprocess
import sys
import traceback


def command_available(command):
    """Returns true iff command can be called without errors.

    command should be a list. For checking the availbability of a command it
    is common prectice to call the command's help method, e.g.

    ['validate', '-h'] or ['minisat', '--help']
    """
    try:
        subprocess.check_call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, OSError) as err:
        return False


def remove(filename):
    """Removes the file under "filename" and catches any errors.

    If filename points to a directory it is not removed.
    """
    try:
        os.remove(filename)
    except OSError:
        pass

def parse_heuristic_params(params_str):
    """
    Convert a string of heuristic parameters into a dictionary.
    Expects parameters in the format: key1=value1, key2=value2, ...
    """
    if not params_str:
        return {}
    
    # Remove any whitespace and split into key=value pairs
    param_pairs = [pair.strip() for pair in params_str.split(',')]
    param_dict = {}
    
    for pair in param_pairs:
        key, value = pair.split('=')
        param_dict[key.strip()] = eval(value.strip())
    
    return param_dict