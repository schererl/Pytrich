import sys

class Operator:
    """
    Attributes:
        @param name: The name of the operator.
        @param hash_name: hashed name for saving computation when hash is needed.
        @param pos_precons: Set of positive preconditions that must be true for the operator to be applicable.
        @param neg_precons: ---
        @param add_effects: Set of effects representing the facts that this operator makes true.
        @param del_effects: A set of effects representing the facts that this operator makes false.
        @param pos_precons_bitwise: Bitwise representation of positive preconditions for efficient computation.
        @param neg_precons_bitwise: ---
        @param add_effects_bitwise: ---
        @param del_effects_bitwise: ---
        @param h_goal_val: Heuristic value related to goal task count heuristics (always 0, necessary for consistency)
    """

    def __init__(self, name, pos_precons, neg_precons, add_effects, del_effects):
        self.name = name
        self.hash_name = hash(name)
        self.pos_precons = frozenset(pos_precons)
        self.neg_precons = frozenset(neg_precons)
        self.add_effects = add_effects
        self.del_effects = del_effects

        self.global_id = -1
        self.pos_precons_bitwise = 0
        self.neg_precons_bitwise = 0
        self.del_effects_bitwise = 0
        self.add_effects_bitwise = 0

        self.h_val = 0

    def applicable_bitwise(self, state_bitwise):
        return ((state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise) and \
               ((state_bitwise & self.neg_precons_bitwise) == 0)
    
    def applicable(self, state):
        return self.pos_precons <= state and self.neg_precons.isdisjoint(state)

    def relaxed_applicable_bitwise(self, state_bitwise):
        return (state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise

    def relaxed_applicable(self, state):
        return self.pos_precons <= state
    
    def apply_bitwise(self, state_bitwise):
        return (state_bitwise & ~self.del_effects_bitwise) | self.add_effects_bitwise
    
    def apply(self, state):
        return (state - self.del_effects) | self.add_effects

    def relaxed_apply_bitwise(self, state_bitwise):
        return state_bitwise | self.add_effects_bitwise

    def relaxed_apply(self, state):
        return state | self.add_effects
        
    def get_add_effects_bitfact(self):
        bitwise_value = self.add_effects_bitwise
        i = 0
        while bitwise_value:
            if bitwise_value & 1:
                yield i
            bitwise_value >>= 1
            i += 1

    def get_precons_bitfact(self):
        bitwise_value = self.pos_precons_bitwise
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
        return f"OP({self.name} {bin(self.pos_precons_bitwise)} {bin(self.neg_precons_bitwise)})"
        s = "OPERATOR %s: " % self.name
        #s+= "pre: %s" % self.preconditions
        
        s+= f"\n  Precons: "
        for pos_pre in self.pos_precons:
            s += f"{pos_pre} "
        for neg_pre in self.neg_precons:
            s += f"not{neg_pre} "

        s+= f"\n  Effects: "
        for add_eff in self.pos_precons:
            s += f"{add_eff} "
        for del_eff in self.neg_precons:
            s += f"not{del_eff} "
        
        s+='\n'
        # for group, facts in [
        #     ("POS_PRE", self.pos_precons),
        #     ("NEG_PRE", self.neg_precons),
        #     ("ADD", self.add_effects),
        #     ("DEL", self.del_effects),
        # ]:
        #     for fact in facts:
        #         s += f"  {group}: {fact}\n"
        return s

    def __repr__(self):
        return f"<Op {self.global_id}:{self.name} >"

class AbstractTask:
    """
        HTN Grounded task, different from Task descibed for the goal
    """ 
    def __init__(self, name):
        """
        @param name of the task containing parameters
        """
        self.name = name
        self.hash_name = hash(name)
        self.decompositions = []
        self.h_val = 0

        self.global_id = -1
        self.op_reach = set() #TaskDecompositionPlus

    def __eq__(self, other):
        return self.name == other.name
    
    def __str__(self):
        return f'GT({self.name} arity {len(self.decompositions)})'
    def __repr__(self):
        return f'<Gt %s>' % self.name
    def __hash__(self):
        return hash(self.hash_name)

class Decomposition:
    def __init__(self, name, pos_precons, neg_precons, compound_task, task_network):
        '''
            @param name:                grounded name of the method, includes the literals used into the method
            @param hash_name:           hashed name for saving computation when hash is needed
            @param compound_task:     grounded task which the decomposition can be decomposed into
            @param pos_precons:         literals using string version. - higher memory usage, more readable
            @param neg_precons:         ----
            @param pos_precons_bitwise: bitwise representatioon - lower memory, faster
            @param neg_precons_bitwise: ----
            @param task_network:        list of subtasks to decompose into, 
                                        points to operators instances (primitives) or tasks instances(abstract)
        '''
        self.name = name
        self.hash_name = hash(name)
        self.compound_task = compound_task
        self.pos_precons = frozenset(pos_precons)
        self.neg_precons = frozenset(neg_precons)
        self.task_network = task_network

        self.global_id = -1
        self.pos_precons_bitwise = 0
        self.neg_precons_bitwise = 0

        self.tsn_hval = 0

    def applicable_bitwise(self, state_bitwise):
        return ((state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise) and \
               ((state_bitwise & self.neg_precons_bitwise) == 0)

    def applicable(self, state):
        return self.pos_precons <= state and self.neg_precons.isdisjoint(state)
    
    def relaxed_applicable_bitwise(self, state_bitwise):
        return (state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise

    def relaxed_applicable(self, state):
        return self.pos_precons <= state
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return self.hash_name
    
    def __repr__(self):
        return f"<D {self.name} >"
    
    def __str__(self):
        s = f"DECOMPOSISITION {self.name}\n"
        #s+= f"  Preconditions: {self.preconditions}\n"
        s+= f"  Precons: "
        for pos_pre in self.pos_precons:
            s += f"{pos_pre} "
        for neg_pre in self.neg_precons:
            s += f"not{neg_pre} "
        
        s += f"\n  Decomposed Task: {self.compound_task}\n"
        s += f"  Task Network: {self.task_network[0:min(5, len(self.task_network))]}\n"
        return s
    
    

class Model:
    def __init__(self, name, facts, initial_state, initial_tn, goals, operators, decompositions, abstract_tasks):
        self.name = name
        self.facts = facts
        self.initial_state = initial_state
        self.goals = goals
        self.initial_tn = initial_tn
        self.operators = operators
        self.decompositions = decompositions
        self.abstract_tasks = abstract_tasks
        self.states = {}

        
        # Global ID info
        self.ifacts_init = 0
        self.ifacts_end = len(self.facts) - 1
        
        self.iop_init = -1
        self.iop_end = -1
        self.iabt_init = -1
        self.iabt_end = -1
        self.idec_init = -1
        self.idec_end = -1
        
        
        self._explicit_to_int = {}
        self._int_to_explicit = {}
        self._goal_bit_pos    = []
        self._remove_panda_top()
    
    def get_component(self, component_id):
        if component_id <= self.ifacts_end:
            return component_id  # a fact is an integer
        
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
    def _remove_panda_top(self):
        self.initial_tn = self.initial_tn [0].decompositions[0].task_network #specific for panda grounder
        for d in self.decompositions:
            if "x__top_method_0" in d.name:
                self.decompositions.remove(d)
                break
        for t in self.abstract_tasks:
            if "x__top__" in t.name:
                self.abstract_tasks.remove(t)
                break
        
    def assign_global_ids(self):
        next_id = len(self.facts)
        
        # Assign global IDs to operators
        for o in self.operators:
            o.global_id = next_id
            next_id += 1
        
        self.iop_init = self.operators[0].global_id
        self.iop_end = self.operators[-1].global_id

        # Check for overlap with facts
        assert self.iop_init not in self._int_to_explicit, (
            'Operator index overlapped with fact index'
        )

        # Assign global IDs to abstract tasks
        for ab_t in self.abstract_tasks:
            ab_t.global_id = next_id
            next_id += 1
        
        self.iabt_init = self.abstract_tasks[0].global_id
        self.iabt_end = self.abstract_tasks[-1].global_id

        # Check for overlap with operators
        assert self.iabt_init > self.iop_end, (
            'Abstract task index overlapped with operator index'
        )

        # Assign global IDs to decompositions
        for d in self.decompositions:
            d.global_id = next_id
            next_id += 1
        
        self.idec_init = self.decompositions[0].global_id
        self.idec_end = self.decompositions[-1].global_id

        # Check for overlap with abstract tasks
        assert self.idec_init > self.iabt_end, (
            'Decomposition index overlapped with abstract task index'
        )


    def goal_reached(self, state, task_network=[]):
        return self.goals <= state and len(task_network) == 0
    
    def relaxed_goal_reached(self, state, task_network=[]):
        return (state & self.goals) == self.goals and len(task_network) == 0

    def apply(self, operator, state):
        return operator.apply_bitwise(state)
       
    def applicable(self, modifier, state):
        return modifier.applicable_bitwise(state)
    
    def methods(self, task):
        return task.decompositions

    def decompose(self, decomposition):
        return decomposition.task_network

    def get_fact_name(self, fact_id):
        return self._int_to_explicit[fact_id]

    def problem_info(self):
        model_info = (
            f"Model info:"
            f"\n\tFacts: {len(self.facts)}"
            f"\n\tAbstract Tasks: {len(self.abstract_tasks)}"
            f"\n\tOperators: {len(self.operators)}"
            f"\n\tDecompositions: {len(self.decompositions)}"
        )
        return model_info
    
    def __str__(self):
        memory_info = (
            f"\nMemory Usage:"
            f"\n\tName: {sys.getsizeof(self.name)} bytes"
            f"\n\tFacts: {sys.getsizeof(self.facts)} bytes"
            f"\n\tInitial State: {sys.getsizeof(self.initial_state)} bytes"
            f"\n\tGoals: {sys.getsizeof(self.goals)} bytes"
            f"\n\tOperators: {sys.getsizeof(self.operators)} bytes"
            f"\n\tInitial Task Network: {sys.getsizeof(self.initial_tn)} bytes"
            f"\n\tDecompositions: {sys.getsizeof(self.decompositions)} bytes"
        )
        return memory_info
    
