# About HTN Pyperplan
This is an ongoing project for HTN planning. The project is inspired by Pyperplan base code, currently unnamed and under development.

**Contact:** scherer.victor98@gmail.com

## Execution Instructions
Requires:
* [pandaPIparser](https://github.com/panda-planner-dev/pandaPIparser)
* [pandaPIgrounder](https://github.com/panda-planner-dev/pandaPIgrounder)
* [pandaPIengine](https://github.com/panda-planner-dev/pandaPIengine)

After compiling them, move to *pandaOpt* folder before executing the planner

**Update and run the extension using the following commands:**
```
git submodule update

python pyperplan/__main__.py <domain> <problem>
```

Example:
```
python3 pyperplan/__main__.py htn-benchmarks/Blocksworld-GTOHP/domain.hddl htn-benchmarks/Blocksworld-GTOHP/p01.hddl 
```
## Running parser tests
```
pip install pytest

pytest pyperplan/parser/test_parser.py 
```

## User Guidance
- Benchmarks are a submodule from: https://github.com/schererl/htn-benchmarks
- At the moment only **total order** planning works

### Command-Line Arguments
The script __main__.py supports the following command-line arguments:

* domain (str): Path to the domain file. Optional if running benchmarks.
* problem (str): Path to the problem file. Required unless running benchmarks.
* -l, --loglevel (str): Set the logging level. Choices are debug, info, warning, error. Default is info.
* -s, --search (str): Search algorithm to use. Choices are Astar, BFS, DFS, Greedy. Default is Astar.
* -H, --heuristic (str): Heuristic to use. Choices are Blind, HAdd, HMax, HFF. Default is Blind.
* -g, --grounder (str): Grounder to use. Choices are panda, native. Default is panda.
* -re, --runExperiment (str): Run a specific experiment. Choices are search, tdglm, landmark, none. Default is none.


### About Grounder
Grounding instantiates tasks, actions, and methods with constants, respecting type hierarchies for search applicability. 
The PANDA grounder, 'pandaGround.py', is currently utilized alongside ongoing optimizations in 'optimize_model.py'. 
There is significant potential for further enhancement in these optimizations.

As mentioned before, the native parser and grounder is not working by now. For future implementation, there is an interface available for the parser.

# To-Do List
### Parser/Grounder
- [ ] (**FIX**) Develop a new HTN parser, possibly consulting Meneguzzi for an example. -Valid contribution
- [ ] (**ADD**) Enhance grounding techniques and their post-processing. -Valid contribution

### Search Improvements
- [ ] (**ADD**) Implement loop detection and dead-end identification, see Maugnuano and Conny Olz's work. -Valid contribution

### Heuristic Development
- [ ] (**ADD**) Integrate IP/LP heuristic approaches (work in progress).
- [ ] (**ADD**) Develop a TDG heuristic tailored for PANDA (work in progress).
- [ ] (**ADD**) Explore HTN landmark heuristics, potentially adapting from Elkawkagy’s work (work in progress).
- [ ] (**ADD**) Research and apply RC compilation strategies. -Valid contribution
