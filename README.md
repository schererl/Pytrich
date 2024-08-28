# HTN Pyperplan Project

## Overview
This project focuses on Hierarchical Task Network (HTN) planning, originally based on the Pyperplan codebase. While it draws inspiration from Pyperplan, it has evolved into a distinct and currently unnamed project that is actively under development.

**Contact:** [scherer.victor98@gmail.com](mailto:scherer.victor98@gmail.com)

## Prerequisites
To run the planner, ensure the following dependencies are installed and compiled:

- [pandaPIparser](https://github.com/panda-planner-dev/pandaPIparser)
- [pandaPIgrounder](https://github.com/panda-planner-dev/pandaPIgrounder)
- [pandaPIengine](https://github.com/panda-planner-dev/pandaPIengine)

After compiling these, move them to `pandaOpt` directory before executing the planner.

## Execution Instructions

1. **Initialize and Update Submodules**
    ```bash
    git submodule init
    cd htn-benchmarks
    git submodule update
    ```

2. **Run the Planner**
    ```bash
    python pyperplan/__main__.py htn-benchmarks/Blocksworld-GTOHP/domain.hddl htn-benchmarks/Blocksworld-GTOHP/p01.hddl 
    ```

## User Guidance

- **Benchmarks**: The benchmarks are included as a submodule from [htn-benchmarks](https://github.com/schererl/htn-benchmarks).
- **Supported Planning Type**: Currently, only **total order** planning is supported.
- **Parser/Grounder**: A custom parser/grounder is not yet implemented; instead, PANDA is used as a grounding subroutine.
- **Scripts**: The `Script` directory contains useful scripts for running experiments.

### Command-Line Arguments
The script `__main__.py` supports the following arguments:

- **domain** (`str`): Path to the domain file. Optional if running benchmarks.
- **problem** (`str`): Path to the problem file. Required unless running benchmarks.
- **-H, --heuristic** (`str`): Heuristic to use. Choices are `Blind`, `TDG`, `LMCOUNT`, `TDGLM`. Default is `TDG`.
- **-hp `<args>`**: Heuristic parameters. Specify parameters for the selected heuristic. Each heuristic has its own parameters, which can be found in the respective class. Example: `-H LMCOUNT -hp "name=\"MyHeuristic\", use_bid=True, use_disj=False"`
- **-g, --grounder** (`str`): Grounder to use. Currently, `panda` is the only option. Default is `panda`.
- **-tor**: Enable Total-Order reachability during grounder post-processing (unpublished).
- **-ms**: Monitor time and memory usage during search.
- **-ml**: Monitor time during landmark generation.
- **-nh**: Disable heuristic output log.
- **-ns**: Disable search output log.
- **-lg**: Enable post-processing grounder output log.

## Ongoing Research
Some aspects of this planner are new and have not been published yet, so please use them responsibly. Below are some of our ongoing projects related to HTN planning:

1. **AND/OR Landmark Generation**: We are developing what we call 'Bidirectional Landmarks,' based on AND/OR graphs.
2. **TO Landmark Generation**: We are exploring the feasibility of computing landmarks that capture ordering constraints, specifically for Total-Order (TO) problems.
3. **TO Grounding**: We are investigating whether the same technique can be used for pruning unreachable regions of the Decomposition Space during grounding.
4. **Landmark Ordering**: We are interested in a novel approach to landmark extraction based on LAMA and exploring whether finding landmark orderings could provide valuable information for the search process.
5. **IP Heuristics**: We are examining how to enhance Integer Programming (IP) heuristics using landmarks and whether they offer useful insights for solving the problem.

## Development Roadmap

### Parser/Grounder
- [ ] **Add:** Develop a new HTN parser/grounder.
- [ ] **Add:** Enhance grounding techniques and post-processing methods.

### Search Improvements
- [ ] **Add:** Implement loop detection and dead-end identification (see Mangunano and Conny Olz's work).
- [ ] **Refactor:** Update search code to allow passing the search method (e.g., Blind, GBFS, A*) as a parameter.

### Heuristic Development
- [ ] **Add:** Integrate IP/LP heuristic approaches (in progress).
- [ ] **Add:** Explore HTN landmark heuristics, potentially adapting methods from Elkawkagy’s work (in progress).
- [ ] **Add:** Research and apply RC compilation strategies.
