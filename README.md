# ABOUT HTN PYPERPLAN
extension of pyperplan for htn under development

## DEBUG FEATURES

* There is a graphviz generator using the DOT_output.py (by now remove the comment '#' form dot call at the blind_search.py)

* Is possible to output the grounding instance in grounder.py, call function export_elements_to_txt

* NO automated tests available yet

## Execution
pip install --editable .

python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl


# TODOS
## UTILS TODOS
- [x] (**ADD**)  GraphViz Visualization -jan24
- [ ] (**ADD**)  Auto check plan validity with IPC23 results
- [x] (**ADD**)  more IPC domains -feb26
- [ ] (**ADD**)  Compute branching factor
- [ ] (**ADD**) models's mem consumption
- [ ] (**ADD**) flags - set heuristics type
- [ ] (**ADD**) flags - set grounder type
- [ ] (**ADD**) flags - set specific or all problems
- [ ] (**ADD**) flags - set timeout grounder and solver

## Heuristic TODOS
- [ ] (**ADD**) IP/LP Heuristic
- [ ] (**ADD**) TDG heursitic - panda
- [ ] (**ADD**) HTN Landmarks - from Elkawkagy
- [x] (**ADD**) TDG heuristic - simple -jan24
- [x] (**ADD**) Goal count heuristics simple (fact and task) -jan24
- [x] (**ADD**) Delete Relaxation heuristic -jan24

## Parser TODOS
- [ ] (**ADD**) ORDERINGS
- [ ] (**ADD**) FORALL
- [x] (**ADD**) CONSTANTS -feb26
- [ ] (**MEMORY**) Variables from Methods and Actions paramaters should be unique and share addresses with effects, subtasks instances etc.
- [ ] Improve parser (too confusing maybe change it completely)


## Grounder TODOS
- [x] (**ADD**) grounder's memory usage limit (only for TDG grounder) -feb26
- [ ] (**OPT**) Type specialization
- [x] (**OPT**) Pullup 04-fev
- [ ] (**FIX**) TDG Grounder RecursionError exception for deep domains
- [ ] (**MEMORY**) Remove lifted structures already grounded
- [ ] (**MEMORY**) (**MODEL CHANGE**) Test if change Decomposition and AbstractTask, instead of pointing to objects in theirs subtasks and compound task, have the index to get into Model. The same for nodes with tasknetworks.
- [x] (**MEMORY**) TDG Grounder
- [x] (**EFFICIENCY**) Grounder post-processing TDG Rechability -jan24
- [x] (**EFFICIENCY**) Grounder post-processing Delete Relaxation simpler version -feb12
- [x] (**CORRECTNESS**) Grounder post-processing remove negative preconditions -jan24
- [x] (**MEMORY**) Grounder post-processing convert facts into bitwise representation -jan24

## Domain TODOS
- [ ] (**FIX**) Childsnack is not working, invalid solutions
- [ ] (**ADD**) Woodworking: constants
- [ ] (**ADD**) Freecell: ordering
- [ ] (**ADD**) Snake: '=' sign without 'not', and forall
- [ ] (**ADD**) Assembly Hierarchichal: ordering
- [ ] (**ADD**) Blocksworld-HPDDL: forall
- [ ] (**MODIF**) Check why Childsnack domain is not getting solutions
- [ ] (**MODIF**) Remove the need for declaring explicitly parent types (e.j original Barman/Barman-BDI domains)
- [ ] (**MODIF**) Some subtasks are in a different formula format, they doesn't have the 'key' only the subtask names (e.j Factories, Factories-simple)
- [ ] (**COMPARE**) Transport domain with panda, why is it too hard for htn-pyperplan?


* The problem with Factories was the empty subtasks. I changed the grounded to check if the subtasks contains None element, For now it works but latter it should create an empty list of subtasks only.
* **TRANSPORT** almost impossible to solve (only the first problem solved)

