# <img src="Icon/pytrich-icon.png" alt="Pytrich Icon" width="40" style="border-radius: 50%;"/> Pytrich HTN Planner

## Overview
**Pytrich** is a progressive search planner for total-order problems in Hierarchical Task Network (HTN).

## Prerequisites
To run the planner, ensure the following dependencies are installed and compiled:

- [pandaPIparser](https://github.com/panda-planner-dev/pandaPIparser)
- [pandaPIgrounder](https://github.com/panda-planner-dev/pandaPIgrounder)


After compiling, place the binaries in the `pandaBuilds` directory before executing the planner.

> **Note:** If you're using Ubuntu 22.04, the precompiled PANDA files included in the project may work without recompilation.

### Compatibility
- **Supported OS:** Ubuntu (tested on Ubuntu 22.04).
- If you're running on a different OS or encounter any issues, please contact us or contribute a fix.

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
### Benchmarks

Benchmarks are included as a submodule from [htn-benchmarks](https://github.com/schererl/htn-benchmarks).

### Supported HTN Planning Type
Currently, only **total order** planning is supported.

### Grounding
The planner currently uses PANDA's grounding subroutine.

### Experiments
The `Experiments` directory contains useful scripts for running experiments and some results of previous experiments.

### Command-Line Arguments
| Argument                  | Description                                                                                     | Default            |
|---------------------------|-------------------------------------------------------------------------------------------------|--------------------|
| **domain and problem**    | Path to the domain and problem file in HDDL format.                                             | Required (if no `--sas_file`). |
| **--sas_file `<file>`**   | Path to a pre-grounded SAS file (does not require domain/problem files).                        | None               |
| **-H, --heuristic `<type>`** | Specify the heuristic to use in the format `heuristic_name(param1=value1,param2=value2)`.       | `TDG()`            |
| **-S, --search `<type>`** | Specify the search algorithm in the format `search_name(param1=value1,param2=value2)`.          | `Astar(use_early=False)`          |
| **-N, --node `<type>`**   | Specify the node type in the format `node_type(param1=value1,param2=value2)`.                   | `AstarNode(G=1,H=1)`      |
| **-tor**                  | Enable Total-Order reachability analysis during grounding.                                      | Disabled           |
| **-ms**                   | Monitor time and memory usage during search.                                                   | Disabled           |
| **-ml**                   | Monitor time during landmark generation.                                                       | Disabled           |
| **-mg**                   | Enable post-processing grounder logging.                                                       | Disabled           |

### Example Usage

```bash
python __main__.py \
    -H "LMCOUNT(use_bid=True)" \
    -S "Astar(use_early)" \
    -N "AstarNode(G=0,H=5)" \
    --sas_file htn-benchmarks/sas_folder/problem.sas
```


## Ongoing Research

1. **Bidirectional Landmarks**: Developing landmarks using an AND/OR graph encoding for HTN planning (paper submitted to ICAPS25).
2. **Total-Order Landmark Generation**: Exploring order constraints in landmark computation (currently under research).
3. **Total-Order Grounding**: Improving pruning in decomposition space (currently under research).
4. **Novelty Search**: Applying novelty heuristics to HTN planning (currently under research).
5. **Integer Programming (IP) Heuristics**: Leveraging landmarks in IP-based heuristics for HTN planning (research interest).
