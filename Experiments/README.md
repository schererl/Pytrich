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
    python python_scripts/statistics_summary.py -i outputs/csv-files/new_experiment/<file_name>.csv -o outputs/csv-files/new_experiment/<file_name>-cov.csv

    # create a plot of expanded nodes comparing two search methods
    python python_scripts/expanded_nodes_plot.py -i outputs/csv-files/new_experiment/<file_name>.csv -o outputs/img-files/new_experiment/<file_name>-<e1>-<e2>.pdf -x <search_method_1> -y <search_method_2>
```

# Experiment Report

### 28/02/25 - Landmark Experimients (including lmc)

**GENERAL IDEA:** Compare all types of landmark generation techniques for HTN planning using simple lm-count heuristic.

* Compared Mandatory Tasks (MT), Bottom-up (BU), Bidirectional (BID) and Landmark-cut (LMC)
* I made a mistake and ran all the experiments using A-star (suppose to use GBFS or WA-star).
Experiments with 8GB ram and 1800 runtime.

### Novelty Experiments (again) with DFS implementation (recursive) 

**GENERAL IDEA:** Use DFS see if is faster and see if novelty helps.

* It didnt  :(

### February -Novelty Experiments

[csv file1 here](Experiments/outputs/csv-files/novelty/novelty-experiments.csv)
[csv file2 here](Experiments/outputs/csv-files/novelty/novelty-experiments-stats.csv)

**GENERAL IDEA:**: Implemented different novelty methods considering different heuristic values.

* The novelty criteria is a tuple w=<h,f,t>, here *h* is a set of heuristics, *f* facts and *t* tasks.

* We use GBFS with the queue (w,h), changing *h*. For validating whether novelty helps to solve more tasks, we typically compared (w,h) x (h).

**EXPERIMENTS DESCRIPTION:**
- lmcount: landmark count using bottom-up landmarks
- TDG-satis: task decomposition graph heuristic satisficing
- Novelty-lm-f-t: novelty with lmcount
- Novelty-lm-tdg-f-t: novelty with lmcount, tdg-satis
- lmcount-tdg: lmcount, tdg
- Novelty-tdg-f-t: novelty, tdg
- Novelty-bid-tdg-f-t: novelty, bidirectional lms, tdg
- Novelty-tdg-bid-f-t: novelty, tdg, bidirectional lms
- Novelty-lmonly_bu-tdg-f-t: novelty <h,f,t>, where h=lmcount, and tdg is tie-breaking.

**SUMMARY TABLE**
|experiment|coverage|avg. plan|avg. nodes|
|-------|-----|-------|---------|
lmcount	|166	|171.90	|536765.72|
Novelty-lm-f-t|178	|161.45	|394222.06|
Novelty-lm-tdg-f-t|179	|173.13	|269436.12|
lmcount-tdg	|210	|393.27	|606909.24|
Novelty-tdg-f-t	|152	|136.75	|538791.76|
TDG-satis|163	|95.66	|875481.77|
Novelty-bid-tdg-f-t	|189	|210.05	|387100.80|
Novelty-tdg-bid-f-t	|164	|225.03	|353564.23|
Novelty-lmonly_bu-tdg-f-t	|180	|205.77	|417151.27|

**CONFIG:**
- Time Limit: 60 seconds per problem instance.
- Memory Limit: ~8 GB.

### 05/01/25
### Search Methods
- **LMCOUNT-update**
- **TDG-satis**
- **\[LMCOUNT-update,TDG-satis\]**
- **\[LMCOUNT-update,TDG-satis,NOVELTY\]**
- **\[TDG-satis,LMCOUNT-update\]**
- **\[TDG-satis,LMCOUNT-update,NOVELTY\]**

More experiments checking if using tie-breaking works.
Search: 5WA*
Search time: 600s
1- The results don't show improvements using multiple heuristics for tie-breaking. 
The coverage using single heuristic tends to be higher and the expanded nodes the same.


### 19/12/24
### Search Methods
- **LMCOUNT-update**
- **TDG-satis**
- **\[LMCOUNT-update,NOVELTY\]**
- **\[TDG-satis, NOVELTY\]**
- **\[TDG-satis, LMCOUNT-update, NOVELTY\]**

Experiments to verify if using novelty as tie-breaking works and to use multiple heuristics as tie-breaking also works.
Search: 5WA*
Search time: 60s
1- The results don't show clear difference of using novelty as tie-breaking helps the heuristic significantly under the tested benchmarks
2- Using all three heuristics don't reduce significantly nodes expanded compared to the single best performant heuristic (tdg-satis)

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
