# Pytrich HTN Planner

## Overview
**Pytrich** is a progressive search planner for total-order problems in Hierarchical Task Network (HTN).

## Prerequisites
To run the planner, ensure the following dependencies are installed and compiled:

- [pandaPIparser](https://github.com/panda-planner-dev/pandaPIparser)
- [pandaPIgrounder](https://github.com/panda-planner-dev/pandaPIgrounder)


After compiling these, move them to `pandaBuilds` directory before executing the planner.

If you use Ubuntu 22.04 probably the compiled panda files in the project will serve and you won't need to build them again

Pytrich was only tested in Ubuntu if you have any problem to run in a different distro or SO, contact us, or contribute to our project.

## Execution Instructions

1. **Initialize and Update Submodules**
    ```bash
    git submodule init
    cd htn-benchmarks
    git submodule update
    ```

2. **Run the Planner**
    ```bash
    python __main__.py htn-benchmarks/Blocksworld-GTOHP/domain.hddl htn-benchmarks/Blocksworld-GTOHP/p01.hddl 
    ```

## User Guidance
- **Benchmarks**: The benchmarks are included as a submodule from [htn-benchmarks](https://github.com/schererl/htn-benchmarks).
- **Supported Planning Type**: Currently, only **total order** planning is supported.
- **Parser/Grounder**: A custom parser/grounder is not yet implemented; instead, PANDA is used as a grounding subroutine.
- **Scripts**: The `Script` directory contains useful scripts for running experiments (not working at the moment).

### Command-Line Arguments
The script `__main__.py` supports the following arguments:

- **domain and problem** (`[domain_file] [problem_file]`): Path to the domain and problem file in HDDL format. 
- **--sas_file `<file>`**: Path to the problem already in sas plus format (don't require including .HDDL domain and problem files).
- **-H, --heuristic `<heuristic_type>`** (`str`): Heuristic to use. Choices are `TDG`, `LMCOUNT`. Default is `TDG`.
- **-s, --search `<search_algorithm>`** (`str`): Search algorithm to use. Choices are `Astar`, `Blind`. Default is `Astar`.
- **-hp `<args>`**: Heuristic parameters. Specify parameters for the selected heuristic. Each heuristic has its own parameters, which can be found in the respective class. Example: `-H LMCOUNT -hp "name=\"MyHeuristic\", use_bid=True, use_ord=False"`
- **-tor**: Enable Total-Order reachability during grounder post-processing (unpublished).
- **-ms**: Monitor time and memory usage during search.
- **-ml**: Monitor time during landmark generation.
- **-mg**: Enable post-processing grounder logging.

## Ongoing Research
Several new components of this planner are currently under research. Key projects include:

1. **AND/OR Landmark Generation**: We are developing what we call **Bidirectional Landmarks** using a new AND/OR encoding for HTN planning.
2. **TO Landmark Generation**: Exploration of Total-Order landmark computation to capture ordering constraints.
3. **TO Grounding**: Pruning unreachable regions in Decomposition Space through Total-Order analysis.
4. **Landmark Ordering**: Investigating landmark ordering to inform search, inspired by LAMA.
5. **IP Heuristics**: Enhancing Integer Programming (IP) heuristics with landmarks for solving HTN planning problems.
6. **Novelty**: Novelty for HTN planning.

## Development Roadmap

### Parser/Grounder
- [ ] **DEVELOP:** Develop a new HTN parser/grounder.
- [ ] **ENHANCE:** grounding techniques and post-processing methods (to-reachability).

### Search Improvements
- [ ] **Add:** Implement task preconditions for TO-HTN (Conny Olz's work).

### Heuristic Development
- [ ] **IN PROGRESS:** Integrate IP/LP heuristic approaches (in progress).
- [ ] **IN PROGRESS:** Explore HTN landmark heuristics (in progress).
- [ ] **IN PROGRESS:** Implement RC compilation strategies.
