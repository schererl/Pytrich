# Experiments Folder

# Experiments Folder

## Scripts

- The `bash_scripts` folder contains:
  - **`benchmark_runner.sh`**: A script to run tests across a set of domains.
  - **`domain_runner.sh`**: A script to run all problems within a single domain.

- The `python_scripts` folder includes:
  1. **`parse_log.py`**: Parses the `.log` file generated after running a runner script and produces a `<file>.csv` output.
  2. **`coverage_summary.py`**: Takes the `<file>-cov.csv` as input and outputs a coverage summary in `.csv` format.
  3. **`expanded_nodes_plot.py`**: Takes the `<file>.csv` as input and generates a PDF plot comparing the expanded nodes for two search methods specified by `-x` and `-y`.

### Example Workflow:
```bash
    # create directories for outputs
    mkdir outputs/log-files/new_experiment
    mkdir outputs/csv-files/new_experiment
    mkdir outputs/img-files/new_experiment

    # run the benchmark script
    bash_scripts/benchmark_runner.sh >> outputs/log-files/new_experiment/<file_name>.log

    # parse the log into a CSV file
    python python_scripts/parse_log.py -i outputs/log-files/new_experiment/<file_name>.log -o outputs/csv-files/new_experiment/<file_name>.csv

    # generate a coverage summary
    python python_scripts/coverage_summary.py -i outputs/csv-files/new_experiment/<file_name>.csv -o outputs/csv-files/new_experiment/<file_name>-cov.csv

    # create a plot of expanded nodes comparing two search methods
    python python_scripts/expanded_nodes_plot.py -i outputs/csv-files/new_experiment/<file_name>.csv -o outputs/img-files/new_experiment/<file_name>-<e1>-<e2>.pdf -x <search_method_1> -y <search_method_2>
```

# Experiment Report

## 29/11/24
### Search Methods
- **LMCOUNT**
- **NOVELTY-FT**
- **NOVELTY-lazyFT**
- **NOVELTY-lmcount**

### Goals
1. Compare **LMCOUNT** vs **NOVELTY-lmcount**.
2. Compare **FT** vs **lazyFT** (Evaluate whether considering the entire task network for novelty generation is better than only using the task associated with the current node).

### Experiment Configurations
- **Time Limit:** 60 seconds per problem instance.
- **Memory Limit:** ~8 GB.
- **Benchmark:** Small benchmarks.

### Search Method Details
#### **LMCOUNT**
- A bottom-up graph-based landmark heuristic.

#### **NOVELTY-FT**
- Novelty is calculated using `FACT x TASK`, defined as the **current state** and the **entire task network**.

#### **NOVELTY-lazyFT**
- Novelty is calculated using `FACT x TASK`, defined as the **current state** and the **current task being applied or decomposed**.

### Observations
- **NOVELTY-lmcount** expanded fewer nodes compared to **LMCOUNT** in nearly every domain.
- **lazyFT** appears more effective than **FT**, but Meneguzzi suggested investigating if this is due to the faster computation of **lazyFT**.

## 28/11/24
### Search Methods
- **Blind**
- **Blind  with preferred Novelty**
- **LMCOUNT**

### Experiment Configurations
- **Time Limit:** 60 seconds per problem instance.
- **Memory Limit:** ~8 GB.

### Search Method Details
#### **Blind Search**
- Implements a typical breadth-first search (BFS) with early goal detection.

#### **Novelty Search**
- Extends Blind Search with two queues:
  - A **preferred queue** for nodes with novelty.
  - A **regular queue** for nodes without novelty.
- Novelty is calculated using `FACT x TASK`, with early goal detection.

#### **LMCOUNT**
- Uses a bottom-up landmark approach combined with A* search.
- Evaluation function parameters: \( G = 1, H = 1 \).
- Does not use early goal detection.
