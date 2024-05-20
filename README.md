# About HTN Pyperplan
This is an ongoing project for HTN planning. The project is inspired by Pyperplan base code, currently unnamed and under development.

**Contact:** scherer.victor98@gmail.com

## Execution Instructions
Update and run the extension using the following commands:


## Execution
```
git submodule update

python3 -po <domain> <problem>
```
Example:
    python3 pyperplan/__main__.py -po benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl


### Key Flags
- **`-po`**: Use the PANDA grounder. The native parser and grounder have some software engineering problems, requiring a complete substitution.
- **`-rb`**: Run benchmarks (`run_benchmarks.py`). Stability is uncertain; troubleshooting and potential fixes are encouraged if issues arise.

## User Guidance
Currently, the most effective heuristic is 'TaskDecomposition'. Development is underway for landmark extraction, which may soon provide additional heuristic options.

- Be aware: landmarks is not admissible, so don't use it for optimal planning.
- Benchmarks are a submodule from: https://github.com/schererl/htn-benchmarks
- At the moment only **total order** planning works

**Blind Search:** 
```
python3 pyperplan/__main__.py -po -s Astar -H Blind benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl
```

**TaskDecomposition:** 
```
python3 pyperplan/__main__.py -po -s Astar -H TaskDecomposition benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl
```

**Landmarks:** 
```
python3 pyperplan/__main__.py -po -s Astar -H Landmarks benchmarks/Blocksworld-GTOHP/domain.hddl benchmarks/Blocksworld-GTOHP/p10.hddl
```



### About Grounder
Grounding instantiates tasks, actions, and methods with constants, respecting type hierarchies for search applicability. 
The PANDA grounder, 'pandaGround.py', is currently utilized alongside ongoing optimizations in 'optimize_model.py'. 
There is significant potential for further enhancement in these optimizations.

As mentioned before, the native parser and grounder is not working by now, and it has a poor software engineering, so Im not using it.

# To-Do List
### Parser/Grounder
- [ ] (**FIX**) Develop a new HTN parser, possibly consulting Meneguzzi for an example. -Valid contribution
- [ ] (**ADD**) Enhance grounding techniques and their post-processing. -Valid contribution

### Search Improvements
- [ ] (**ADD**) Implement loop detection and dead-end identification, see Maugnauano and Conny Olz's work. -Valid contribution

### Heuristic Development
- [ ] (**ADD**) Integrate IP/LP heuristic approaches (work in progress).
- [ ] (**ADD**) Develop a TDG heuristic tailored for PANDA (work in progress).
- [ ] (**ADD**) Explore HTN landmark heuristics, potentially adapting from Elkawkagy’s work (work in progress).
- [ ] (**ADD**) Research and apply RC compilation strategies. -Valid contribution
