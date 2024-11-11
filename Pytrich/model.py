import sys
from typing import List, Union

from Pytrich.DESCRIPTIONS import Descriptions

class Fact:
    def __init__(self, name, local_id, global_id):
        self.name = name
        self.hash_name = hash(name)
        self.global_id:int = global_id
        self.local_id:int  = local_id
    
    def __eq__(self, other):
        return (
            self.name == other.name
        )

    def __hash__(self):
        return  self.hash_name

    def __str__(self):
        return f"F({self.name} ({self.global_id}))"
        
    def __repr__(self):
        return f"<F{self.global_id}:{self.name} >"

class Operator:
    def __init__(self, global_id, local_id, name, cost, pos_precons, neg_precons, add_effects, del_effects):
        self.name = name
        self.hash_name = hash(name)
        self.global_id:int = global_id
        self.local_id:int  = local_id

        self.cost:int = cost
        self.pos_precons:int = pos_precons
        self.neg_precons:int = neg_precons
        self.del_effects:int = del_effects
        self.add_effects:int = add_effects
        

    def applicable(self, state_bitwise):
        return ((state_bitwise & self.pos_precons) == self.pos_precons) and \
               ((state_bitwise & self.neg_precons) == 0)
    
    def apply(self, state_bitwise):
        return (state_bitwise & ~self.del_effects) | self.add_effects
    
    def relaxed_apply(self, state_bitwise):
        return state_bitwise | self.add_effects
        
    def get_add_effects(self):
        bitwise_value = self.add_effects
        i = 0
        while bitwise_value:
            if bitwise_value & 1:
                yield i
            bitwise_value >>= 1
            i += 1

    def get_precons(self):
        bitwise_value = self.pos_precons
        i = 0
        while bitwise_value:
            if bitwise_value & 1:
                yield i
            bitwise_value >>= 1
            i += 1

    def __eq__(self, other):
        return (
            self.name == other.name
        )

    def __hash__(self):
        return  self.hash_name

    def __str__(self):
        return f"OP({self.name} {bin(self.pos_precons)} {bin(self.neg_precons)})"
        
    def __repr__(self):
        return f"<Op {self.global_id}:{self.name} >"

class AbstractTask:
    def __init__(self, global_id, local_id, decompositions, name):
        self.name = name
        self.hash_name = hash(name)
        self.decompositions: List[Decomposition] = decompositions
        self.global_id:int = global_id
        self.local_id:int  = local_id
        
    def __eq__(self, other):
        return self.name == other.name
    
    def __str__(self):
        return f'GT({self.name} arity {len(self.decompositions)})'
    def __repr__(self):
        return f'<Gt %s>' % self.name
    def __hash__(self):
        return hash(self.hash_name)

class Decomposition:
    def __init__(self, name, global_id, local_id, pos_precons, neg_precons, compound_task, task_network):
        self.name = name
        self.hash_name = hash(name)
        self.global_id:int = global_id
        self.local_id:int  = local_id

        self.compound_task:AbstractTask = compound_task
        self.task_network:List[Union[Operator, AbstractTask]] = task_network
        self.pos_precons:int = pos_precons
        self.neg_precons:int = neg_precons

    def applicable(self, state_bitwise):
        return ((state_bitwise & self.pos_precons) == self.pos_precons) and \
               ((state_bitwise & self.neg_precons) == 0)

    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return self.hash_name
    
    def __repr__(self):
        return f"<D {self.name} {self.task_network} >"
    
    def __str__(self):
        s = f"DECOMPOSISITION {self.name}\n"
        s += f"\tDecomposed Task: {self.compound_task}\n"
        s += f"\tTask Network: {self.task_network[0:min(5, len(self.task_network))]}\n"
        return s
    
    

class Model:
    def __init__(self, facts: set, initial_state: set, initial_tn: List[Union[Operator, AbstractTask]],
                 goals: set, operators: List[Operator], decompositions: List[Decomposition], 
                 abstract_tasks: List[AbstractTask]):
        self.facts = facts
        self.initial_state = initial_state
        self.goals = goals
        self.initial_tn = initial_tn
        self.operators = operators
        self.decompositions = decompositions
        self.abstract_tasks = abstract_tasks
        
        self.desc = Descriptions()

        # Global ID info: initial (init) and final (end) global indixes for facts, operators, abstract_tasks, and decompositions
        self.ifacts_init = 0
        self.ifacts_end  = len(self.facts) - 1
        self.iop_init  = self.ifacts_end+1
        self.iop_end   = self.iop_init + len(self.operators)-1
        self.iabt_init = self.iop_end + 1
        self.iabt_end  = self.iabt_init + len(self.abstract_tasks)-1
        self.idec_init = self.iabt_end+1
        self.idec_end  = self.idec_init + len(self.decompositions)-1
        
        #self._remove_panda_top()
    
    def get_component(self, component_id):
        if component_id <= self.ifacts_end:
            fact=self.facts[component_id]
            assert fact.global_id == component_id, (
                f'FACT COMPONENT INDEXING FAILED: expected {component_id}, got {fact.global_id}'
            )
            return self.facts[component_id]
        
        if component_id >= self.iop_init and component_id <= self.iop_end:
            operator = self.operators[component_id - self.iop_init]
            assert operator.global_id == component_id, (
                f'OPERATOR COMPONENT INDEXING FAILED: expected {component_id}, got {operator.global_id}'
            )
            return operator
        
        if component_id >= self.iabt_init and component_id <= self.iabt_end:
            abstract_task = self.abstract_tasks[component_id - self.iabt_init]
            assert abstract_task.global_id == component_id, (
                f'ABSTRACT TASK COMPONENT INDEXING FAILED: expected {component_id}, got {abstract_task.global_id}'
            )
            return abstract_task
        
        if component_id >= self.idec_init and component_id <= self.idec_end:
            decomposition = self.decompositions[component_id - self.idec_init]
            assert decomposition.global_id == component_id, (
                f'DECOMPOSITION COMPONENT INDEXING FAILED: expected {component_id}, got {decomposition.global_id}'
            )
            return decomposition

        raise ValueError(f'Invalid component_id: {component_id}')

            
    #NOTE: remove artificial _top task and method added by panda 
    # def _remove_panda_top(self):
    #     self.initial_tn = self.initial_tn [0].decompositions[0].task_network #specific for panda grounder
    #     for d in self.decompositions:
    #         if "x__top_method_0" in d.name:
    #             self.decompositions.remove(d)
    #             break
    #     for t in self.abstract_tasks:
    #         if "x__top__" in t.name:
    #             self.abstract_tasks.remove(t)
    #             break
        
    # def assign_global_ids(self):
    #     next_id = len(self.facts)
        
    #     # Assign global IDs to operators
    #     for o in self.operators:
    #         o.global_id = next_id
    #         next_id += 1
        
    #     self.iop_init = self.operators[0].global_id
    #     self.iop_end = self.operators[-1].global_id

    #     # Check for overlap with facts
    #     assert self.iop_init not in self._int_to_explicit, (
    #         'Operator index overlapped with fact index'
    #     )

    #     # Assign global IDs to abstract tasks
    #     for ab_t in self.abstract_tasks:
    #         ab_t.global_id = next_id
    #         next_id += 1
        
    #     self.iabt_init = self.abstract_tasks[0].global_id
    #     self.iabt_end = self.abstract_tasks[-1].global_id

    #     # Check for overlap with operators
    #     assert self.iabt_init > self.iop_end, (
    #         'Abstract task index overlapped with operator index'
    #     )

    #     # Assign global IDs to decompositions
    #     for d in self.decompositions:
    #         d.global_id = next_id
    #         next_id += 1
        
    #     self.idec_init = self.decompositions[0].global_id
    #     self.idec_end = self.decompositions[-1].global_id

    #     # Check for overlap with abstract tasks
    #     assert self.idec_init > self.iabt_end, (
    #         'Decomposition index overlapped with abstract task index'
    #     )

    def state_explicit_repr(self, state):
        return [self.facts[bit_pos].name for bit_pos in range(state.bit_length()) if state & 1<<bit_pos]

    def goal_reached(self, state, task_network=[]):
        return self.goals <= state and len(task_network) == 0
    
    def problem_info(self):
        model_info = (
            f"Model info:"
            f"\n\t{self.desc('fact_model', len(self.facts))}"
            f"\n\t{self.desc('abstract_task_model', len(self.abstract_tasks))}"
            f"\n\t{self.desc('operator_model', len(self.operators))}"
            f"\n\t{self.desc('decomposition_model', len(self.decompositions))}"
        )
        return model_info
    
    def __str__(self):
        memory_info = (
            f"\nMemory Usage:"
            f"\n\tFacts: {sys.getsizeof(self.facts)} bytes"
            f"\n\tInitial State: {sys.getsizeof(self.initial_state)} bytes"
            f"\n\tGoals: {sys.getsizeof(self.goals)} bytes"
            f"\n\tOperators: {sys.getsizeof(self.operators)} bytes"
            f"\n\tInitial Task Network: {sys.getsizeof(self.initial_tn)} bytes"
            f"\n\tDecompositions: {sys.getsizeof(self.decompositions)} bytes"
        )
        return memory_info
    
