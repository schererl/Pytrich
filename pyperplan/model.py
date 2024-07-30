#
# This file is part of pyperplan.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
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
        return "<Op %s>" % self.name

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
    """
    A STRIPS planning task
    """
    # OP classes for diferetiating literal representation with string and int
    class BitwiseOP():
        @staticmethod
        def goal_reached(state, goals, task_network):
            return (state & goals) == goals and len(task_network) == 0
        @staticmethod
        def apply(operator, state):
            return operator.apply_bitwise(state)
        @staticmethod
        def applicable(modifier, state):
            return modifier.applicable_bitwise(state)
    class StringOP():
        @staticmethod
        def goal_reached(state, goals, task_network):
            return goals <= state and len(task_network) == 0
        @staticmethod
        def apply(operator, state):
            return operator.apply(state)
        @staticmethod
        def applicable(modifier, state):
            return modifier.applicable(state)

    # TODO: change operators and decompositions to set()
    # TODO: remove goal counting stuff, not using it anymore
    # TODO: create a fact class mapping fact names with its correspondent ID
    # TODO: add a model parameters mapping global IDs with its correspondent structure (fact, operator, abstract task or decomposition)
    def __init__(self, name, facts, initial_state, initial_tn, goals, operators, decompositions, abstract_tasks, operation_type = BitwiseOP):
        
        """
        Initializes a planning model with its properties.
        @param name: The name of the planning task.
        @param facts: A set of all fact names in the domain.
        @param initial_state: The initial state of the planning task.
        @param goals: The goal state(s) of the planning task.
        @param operators: A set of operator instances for the domain.
        @param initial_tn: The initial task network for HTN planning.
        @param decompositions: A set of decomposition instances for HTN planning.
        @param operation_type: Type of operations we are using for representing literals (string or int)
        """
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
        
        

        self.operation_type = operation_type
        
        self._explicit_to_int = {}
        self._int_to_explicit = {}
        self._goal_bit_pos    = []
        self._fix_initial_task_network()
    
    def get_component(self, component_id):
        if component_id <= self.ifacts_end:
            return component_id # a fact is an integer
        if component_id >= self.iop_init and component_id <= self.iop_end:
            operator = self.operators[component_id-self.iop_init]
            if operator.global_id != component_id:
                print(f'OPERATOR COMPONENT INDEXING FAILED id: {operator.global_id} desired: {component_id}')
                exit(0)
            return operator
        if component_id >= self.iabt_init and component_id <= self.iabt_end:
            abstract_task = self.abstract_tasks[component_id-self.iabt_init]
            if abstract_task.global_id != component_id:
                print(f'ABSTRACT TASK COMPONENT INDEXING FAILED id: {abstract_task.global_id} desired: {component_id}')
                exit(0)
            return abstract_task
        if component_id >= self.idec_init and component_id <= self.idec_end:
            decomposition = self.decompositions[component_id-self.idec_init]
            if decomposition.global_id != component_id:
                print(f'DECOMPOSITION COMPONENT INDEXING FAILED  id: {decomposition.global_id}  desired: {component_id}')
                exit(0)
            return decomposition
            
    #NOTE: PANDA GROUNDER ALERT, remove _top task and method
    def _fix_initial_task_network(self):
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
        
        for o in self.operators:
            o.global_id = next_id
            next_id+=1
        
        self.iop_init = self.operators[0].global_id
        self.iop_end = self.operators[-1].global_id
        if self.iop_init in self._int_to_explicit:
            print(f'operator index overlapped fact index')
            exit(0)


        for ab_t in self.abstract_tasks:
            ab_t.global_id = next_id
            next_id+=1
        self.iabt_init = self.abstract_tasks[0].global_id
        self.iabt_end = self.abstract_tasks[-1].global_id
        
        for d in self.decompositions:
            d.global_id = next_id
            next_id+=1
        self.idec_init = self.decompositions[0].global_id
        self.idec_end = self.decompositions[-1].global_id

    def goal_reached(self, state, task_network=[]):
        return self.operation_type.goal_reached(state, self.goals, task_network)
    
    def relaxed_goal_reached(self, state, task_network=[]):
        return (state & self.goals) == self.goals

    def apply(self, operator, state):
        return self.operation_type.apply(operator, state)
       
    def applicable(self, modifier, state):
        return self.operation_type.applicable(modifier, state)
    
    def methods(self, task):
        return task.decompositions 

    def decompose(self, decomposition):
        return decomposition.task_network

    def get_fact_name(self, fact_id):
        return self._int_to_explicit[fact_id]

    def count_positive_binary_facts(self, state):
        binary_str = bin(state)[2:] 
        binary_str = binary_str[::-1]
        count=0
        for i, bit in enumerate(binary_str):
            if int(bit) == 1:
                count+=1
        return count

    def print_binary_state_info(self, state):
        binary_str = bin(state)[2:]  # Convert state to binary string, remove the '0b' prefix
        binary_str = binary_str[::-1]  # Reverse it to start from the least significant bit (LSB)
        s = []
        #print(f"Binary representation (LSB to MSB): {binary_str}")
        facts_str = '['
        for i, bit in enumerate(binary_str):
            #print(f"Bit position: {i}, Bit value: {bit} - {self._int_to_explicit[i] }")
            if int(bit) == 1:
                facts_str += f'{self._int_to_explicit[i]} ({i})\n'
                s.append(self._int_to_explicit[i])
        facts_str += ']'
        return facts_str, s
      
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
        #s = f"Model {self.name}\n  Vars:  {', '.join(self.facts)}\n  Init:  {', '.join(self.initial_state)}\n  Goals: {self.goals}{memory_info}"
        #s = f"Model {self.name}\n Goals: {self.goals}{memory_info}"
        return memory_info

    def __repr__(self):
        string = "<Model {0}, vars: {1}, operators: {2}, decompositions: {3}>"
        return string.format(self.name, len(self.facts), len(self.operators), len(self.decompositions))
