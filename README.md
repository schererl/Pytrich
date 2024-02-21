# ABOUT HTN PYPERPLAN
extension of pyperplan for htn under development

**TODOS**
[] TDG Grounder *UNDER DEVELOPMENT*
[] Add grounder's memory usage limit (only for TDG grounder)
[] Add more IPC domains
[] Auto check plan validity with IPC23 results
[] Add flags - set heuristics type
[] Add flag  - set grounder type
[] Add flag  - set specific or all problems
[] IP/LP Heuristic
[] TDG heursitic - panda
[] Improve parser (too confusing)
[x] TDG heuristic - simple -jan24
[x] Goal count heuristics simple (fact and task) -jan24
[x] Delete Relaxation heuristic -feb24
[x] GraphViz Visualization -feb24
[x] Grounder postprocessing TDG Rechability -feb24
[x] Grounder postprocessing Delete Relaxation simpler version -feb24
[x] Grounder postprocessing remove negative preconditiions -jan24
[x] Grounder postprocessing convert facts into bitwise representaion -jan24

## Execution
pip install --editable .
python3 pyperplan/__main__.py benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl

