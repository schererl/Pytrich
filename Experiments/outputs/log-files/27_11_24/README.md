# 27/11/2024

## First Experiment with Novelty
### Experiment Parameters:

- Search Techniques: Novelty, Blind, and LM-Cut (bottom-up)
- Memory Limit: 8 GB RAM
- Time Limit: 180 seconds

### Description:

We conducted a blind search incorporating a novelty criterion based on the combination of facts and tasks (F × T). The novelty value is set to 1 if a state is novel and 0 if it is not.

To manage the search nodes, we used two FIFO queues:
- Preferred Queue: Contains nodes with a novelty value of 1.
- Non-Preferred Queue: Contains nodes with a novelty value of 0.

This approach allows us to prioritize novel states during the search process, potentially improving the efficiency and effectiveness of the planning algorithm.