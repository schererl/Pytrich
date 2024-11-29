# Experiment Report

**Date:** 28/11/24

## Search Methods Overview
This experiment compared three search methods: **Blind**, **Novelty**, and **LMCOUNT**.

- **Blind Search:**
  - Implements a typical breadth-first search (BFS) with early goal detection.
  
- **Novelty Search:**
  - Extends Blind Search using two queues:
    - Preferred queue for nodes with novelty.
    - Regular queue for nodes without novelty.
  - Novelty is calculated using `FACT x TASK` with early goal detection.
  
- **LMCOUNT:**
  - Uses a bottom-up landmark approach with A* search.
  - Evaluation functions: \( G = 1 \), \( H = 1 \).
  - Does not employ early goal detection.

## Experiment Configurations
- **Time Limit:** 60 seconds per problem instance.
- **Memory Limit:** ~8 GB.

## Coverage Results

| Domain                     | Experiment Name | Coverage | Avg. Solution Size |
|----------------------------|-----------------|----------|--------------------|
| AssemblyHierarchical       | NOVELTY         | 2        | 5.00               |
| AssemblyHierarchical       | BLIND           | 2        | 5.00               |
| AssemblyHierarchical       | LMCOUNT         | 2        | 5.00               |
| Barman-BDI                 | NOVELTY         | 4        | 22.25              |
| Barman-BDI                 | BLIND           | 2        | 17.00              |
| Barman-BDI                 | LMCOUNT         | 3        | 19.00              |
| Blocksworld-GTOHP          | NOVELTY         | 13       | 104.46             |
| Blocksworld-GTOHP          | BLIND           | 14       | 98.00              |
| Blocksworld-GTOHP          | LMCOUNT         | 13       | 94.23              |
| Blocksworld-HPDDL          | LMCOUNT         | 5        | 66.20              |
| Blocksworld-HPDDL          | NOVELTY         | 3        | 43.00              |
| Blocksworld-HPDDL          | BLIND           | 2        | 31.50              |
| Depots                     | NOVELTY         | 15       | 58.07              |
| Depots                     | LMCOUNT         | 15       | 58.07              |
| Depots                     | BLIND           | 13       | 52.54              |
| Factories-simple           | BLIND           | 5        | 110.00             |
| Factories-simple           | LMCOUNT         | 5        | 110.00             |
| Factories-simple           | NOVELTY         | 4        | 61.50              |
| Hiking                     | NOVELTY         | 1        | 26.00              |
| Minecraft-Regular          | NOVELTY         | 12       | 84.25              |
| Minecraft-Regular          | LMCOUNT         | 12       | 84.25              |
| Monroe-Fully-Observable    | BLIND           | 10       | 18.90              |
| Monroe-Fully-Observable    | LMCOUNT         | 10       | 18.90              |
| Monroe-Fully-Observable    | NOVELTY         | 2        | 7.00               |
| Monroe-Partially-Observable| NOVELTY         | 1        | 6.00               |
| Monroe-Partially-Observable| BLIND           | 4        | 9.75               |
| Monroe-Partially-Observable| LMCOUNT         | 6        | 17.50              |
| Multiarm-Blocksworld       | NOVELTY         | 4        | 33.75              |
| Multiarm-Blocksworld       | LMCOUNT         | 5        | 37.80              |
| Multiarm-Blocksworld       | BLIND           | 3        | 28.67              |
| Robot                      | NOVELTY         | 11       | 12.36              |
| Robot                      | BLIND           | 11       | 12.36              |
| Robot                      | LMCOUNT         | 11       | 12.64              |
| Rover-GTOHP                | NOVELTY         | 8        | 44.12              |
| Rover-GTOHP                | BLIND           | 7        | 34.86              |
| Rover-GTOHP                | LMCOUNT         | 7        | 34.86              |
| Satellite-GTOHP            | NOVELTY         | 4        | 23.50              |
| Satellite-GTOHP            | BLIND           | 3        | 15.33              |
| Satellite-GTOHP            | LMCOUNT         | 4        | 27.25              |
| Snake                      | NOVELTY         | 2        | 24.50              |
| Snake                      | BLIND           | 2        | 24.50              |
| Snake                      | LMCOUNT         | 2        | 24.50              |
| Towers                     | NOVELTY         | 11       | 371.18             |
| Towers                     | BLIND           | 11       | 371.18             |
| Towers                     | LMCOUNT         | 11       | 371.18             |
| Transport                  | NOVELTY         | 9        | 23.78              |
| Transport                  | BLIND           | 1        | 8.00               |

---
