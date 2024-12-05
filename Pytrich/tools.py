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

def parse_search_params(params_str):
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

def parse_argument_string(heuristic_string):
    import re
    pattern = r"(\w+)\((.*?)\)"
    match = re.match(pattern, heuristic_string)
    if not match:
        raise ValueError(f"Invalid heuristic format: {heuristic_string}")
    heuristic_name, params = match.groups()
    param_dict = {}
    if params:
        for param in params.split(','):
            key, value = param.split('=')
            try:
                param_dict[key.strip()] = eval(value.strip())
            except NameError:
                param_dict[key.strip()] = value.strip()
    return heuristic_name, param_dict

class InvalidArgumentException(Exception):
    pass