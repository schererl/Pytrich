# Experiments Folder

# Experiment Report

## 29/11/24
This experiment compared three search methods: **LMCOUNT**, **NOVELTY-FT**, **NOVELTY-lazyFT**, **NOVELTY-lmcount**.
### **Blind Search:**
  - Implements a typical breadth-first search (BFS) with early goal detection.  
### **Novelty Search:**
  - Extends Blind Search using two queues:
    - Preferred queue for nodes with novelty.
    - Regular queue for nodes without novelty.
  - Novelty is calculated using `FACT x TASK` with early goal detection.  
### **LMCOUNT:**
  - Uses a bottom-up landmark approach with A* search.
  - Evaluation functions: \( G = 1 \), \( H = 1 \).
  - Does not employ early goal detection.
### Experiment Configurations
- **Time Limit:** 60 seconds per problem instance.
- **Memory Limit:** ~8 GB.

## 28/11/24
This experiment compared three search methods: **Blind**, **Novelty**, and **LMCOUNT**.
### **Blind Search:**
  - Implements a typical breadth-first search (BFS) with early goal detection.  
### **Novelty Search:**
  - Extends Blind Search using two queues:
    - Preferred queue for nodes with novelty.
    - Regular queue for nodes without novelty.
  - Novelty is calculated using `FACT x TASK` with early goal detection.  
### **LMCOUNT:**
  - Uses a bottom-up landmark approach with A* search.
  - Evaluation functions: \( G = 1 \), \( H = 1 \).
  - Does not employ early goal detection.
### Experiment Configurations
- **Time Limit:** 60 seconds per problem instance.
- **Memory Limit:** ~8 GB.


