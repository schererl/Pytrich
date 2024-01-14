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
import logging
import sys
from functools import lru_cache
"""
Classes for representing a STRIPS planning task
"""
# class Preconditions:
#     def __init__(self, operator, operands=[]):
#         self._operator = operator
#         self._operands = operands

#     def evaluate(self, state):
#         if self._operator == LogicalOperator.NOOP:
#             return True
#         elif self._operator ==  LogicalOperator.LITERAL:
#             return self._operands in state
#         elif self._operator == LogicalOperator.AND:
#             return all(operand.evaluate(state) for operand in self._operands)
#         elif self._operator ==  LogicalOperator.OR:
#             return any(operand.evaluate(state) for operand in self._operands)
#         elif self._operator ==  LogicalOperator.NOT:
#             assert len(self._operands) == 1
#             return not self._operands[0].evaluate(state)
#         elif self._operator == LogicalOperator.EQUAL:
#             assert len(self._operands) == 2
#             return self._operands[0] == self._operands[1]
        
#     def __repr__(self):
#         return f"Formula(operator={self._operator}, operands={self._operands!r})"

#     def __str__(self):
#         if self._operator == LogicalOperator.NOOP:
#             return 'NOOP'
#         elif self._operator == LogicalOperator.LITERAL:
#             return str(self._operands) if self._operands else 'Empty Literal'
#         return f"{self._operator.name}({self._operands})"

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

        self.pos_precons_bitwise = 0
        self.neg_precons_bitwise = 0
        self.del_effects_bitwise = 0
        self.add_effects_bitwise = 0

        self.h_goal_val = 0

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
        
    def __eq__(self, other):
        return (
            self.name == other.name
        )

    def __hash__(self):
        return  self.hash_name

    def __str__(self):
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

class GroundedTask:
    """
        HTN Grounded task, different from Task descibed for the goal
    """ 
    def __init__(self, name):
        """
        @param name of the task containing parameters
        """
        self.name = name
        self.hash_name = hash(name)
        self.h_goal_val = 0
        self.decompositions = []
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __str__(self):
        return f'GT({self.name})'
    def __repr__(self):
        return f'<Gt %s>' % self.name
    def __hash__(self):
        return hash(self.hash_name)

class Decomposition:
    def __init__(self, name, pos_precons, neg_precons, decomposed_task, task_network):
        '''
            @param name:                grounded name of the method, includes the literals used into the method
            @param hash_name:           hashed name for saving computation when hash is needed
            @param decomposed_task:     grounded task which the decomposition can be decomposed into
            @param pos_precons:         literals using string version. - higher memory usage, more readable
            @param neg_precons:         ----
            @param pos_precons_bitwise: bitwise representatioon - lower memory, faster
            @param neg_precons_bitwise: ----
            @param task_network:        list of subtasks to decompose into, 
                                        points to operators instances (primitives) or tasks instances(abstract)
        '''
        self.name = name
        self.hash_name = hash(name)
        self.decomposed_task = decomposed_task
        self.pos_precons = frozenset(pos_precons)
        self.neg_precons = frozenset(neg_precons)
        self.task_network = task_network
        self.pos_precons_bitwise = 0
        self.neg_precons_bitwise = 0

    def applicable_bitwise(self, state_bitwise):
        return ((state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise) and \
               ((state_bitwise & self.neg_precons_bitwise) == 0)

    def applicable(self, state):
        return self.pos_precons <= state and self.neg_precons.isdisjoint(state)
    
    def relaxed_applicable_bitwise(self, state_bitwise):
        return (state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise

    def relaxed_applicable(self, state):
        return self.pos_precons <= state
        
    def task_network(self, state):
        return self.task_network
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return self.hash_name
    
    def __repr__(self):
        return f"<D {self.name} {self.decomposed_task}>"
    
    def __str__(self):
        s = f"DECOMPOSISITION {self.name}\n"
        #s+= f"  Preconditions: {self.preconditions}\n"
        s+= f"  Precons: "
        for pos_pre in self.pos_precons:
            s += f"{pos_pre} "
        for neg_pre in self.neg_precons:
            s += f"not{neg_pre} "
        
        s += f"\n  Decomposed Task: {self.decomposed_task}\n"
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

    def __init__(self, name, facts, initial_state, initial_tn, goals, operators, decompositions, asbtract_tasks, literal_type = int):
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
        self.operators = operators
        self.initial_tn = initial_tn
        self.decompositions = decompositions
        self.asbtract_tasks = asbtract_tasks
        self.states = {}
        
        # goal count control
        self.count_goal_facts = len(self.goals)
        self.count_goal_tasks = 0
        
        # model optimizations 
        self._compress_model_repr()
        self._process_negative_precons()      #NOTE: suggest to use it after compressing the model
        self._process_goal_task_count()       #NOTE: before converting into bit representation, add task counts into grounded tasks
        self._process_goal_facts_count()      #NOTE: before converting into bit representation, add facts counts into operators
        self._process_goal_task_count()
        
        if literal_type:
            self._explicit_to_int = {}
            self._int_to_explicit = {}
            self._compress_facts_repr(self.facts) #NOTE: won't work without compress_model (facts are empty before it)
            self.operation_type = self.BitwiseOP

    # goal count heuristics
    def _process_goal_facts_count(self):
        pass

    def _process_goal_task_count(self):
        self.count_goal_tasks = len(self.initial_tn)
        for t in self.asbtract_tasks:
            if t in self.initial_tn:
                t.h_goal_val = 1
            
    def goal_reached(self, state, task_network=[]):
        return self.operation_type.goal_reached(state, self.goals, task_network)
    
    def apply(self, operator, state):
        return self.operation_type.apply(operator, state)
       
    def applicable(self, modifier, state):
        return self.operation_type.applicable(modifier, state)
    
    def methods(self, task):
        return task.decompositions 

    def decompose(self, decomposition):
        return decomposition.task_network
         
    ### REMOVE NEGATIVE PRECONDITIONS ###
    # NOTE: some test indicate that this leads to a slightly improve into search time
    def _process_negative_precons(self):
        neg_facts = set()
    
        # convert negative preconditions into 'neg literals'
        for o in self.operators:
            new_pos_precons = set(o.pos_precons)
            for n_p in o.neg_precons:
                new_fact = '(not_' + n_p[1:]
                new_pos_precons.add(new_fact)
                self.facts.add(new_fact)
            neg_facts.update(o.neg_precons)
            o.pos_precons = frozenset(new_pos_precons)

        for d in self.decompositions:
            new_pos_precons = set(d.pos_precons)
            for n_p in d.neg_precons:
                new_fact = '(not_' + n_p[1:]
                new_pos_precons.add(new_fact)
                self.facts.add(new_fact)
            neg_facts.update(d.neg_precons)
            d.pos_precons = frozenset(new_pos_precons)
        
        # change effects to turns a not literals true when modified
        for o in self.operators:
            for fact in o.add_effects:
                if fact in neg_facts:
                    o.del_effects.add('(not_' + fact[1:])
            for fact in o.del_effects:
                if fact in neg_facts:
                    o.add_effects.add('(not_' + fact[1:])
        
        # update initial state
        for fact in neg_facts:
            new_initial_state = set()
            if not fact in self.initial_state:
                new_initial_state.add('(not_' + fact[1:])
            new_initial_state.update(self.initial_state)
            self.initial_state = frozenset(new_initial_state)
            
        #clear all negative precons
        for o in self.operators:
            o.neg_precons=frozenset()
        for d in self.decompositions:
            d.neg_precons=frozenset()
            
    ### OPTIMIZING MODEL ### 
    def _compress_model_repr(self):
        """
        Compresses the model representation to optimize memory usage and performance.

        It filters out unused operators and decompositions based on the initial task network,
        and updates the model with only the necessary elements.
        It also logs the memory usage before and after the compression for profiling purposes.

        NOTE: Less eficient than rechability analysis -it doesnt consider preconditions, neither
        simplify used operators and decompositions by removing dispensable literals.
        """
        used_operators = []
        used_decompositions = []
        used_abstract_tasks = []
        tasks = self.initial_tn[:]
        visited_tasks = set()
        used_facts = set()
        
        for l in self.initial_state:
            used_facts.add(l)
        
        while len(tasks)>0:
            task = tasks.pop()
            if task in visited_tasks:
                continue
            visited_tasks.add(task)
            if type(task) == Operator:
                used_operators.append(task)
                used_facts.update(task.pos_precons) 
                used_facts.update(task.neg_precons)
                used_facts.update(task.add_effects)
                used_facts.update(task.del_effects)
            else:
                used_abstract_tasks.append(task)
                for method in self.methods(task):
                    used_decompositions.append(method)
                    used_facts.update(method.pos_precons)
                    used_facts.update(method.neg_precons)
                    tasks+= self.decompose(method)[:]

        # profilling stuff
        op_before = sys.getsizeof(self.operators) 
        decomp_before = sys.getsizeof(self.decompositions) 
        abs_tasks_before = sys.getsizeof(self.asbtract_tasks) 
        self.operators = used_operators
        self.decompositions = used_decompositions
        self.facts = used_facts
        self.asbtract_tasks = used_abstract_tasks
        op_after = sys.getsizeof(self.operators) 
        decomp_after = sys.getsizeof(self.decompositions)
        tasks_after = sys.getsizeof(self.asbtract_tasks)
        logging.info(f"cleaning operators: before {op_before} bytes ==> after {op_after} bytes")
        logging.info(f"cleaning decompositions: before {decomp_before} bytes ==> after {decomp_after} bytes")
        logging.info(f"cleaning tasks: before {abs_tasks_before} bytes ==> after {tasks_after} bytes")
        logging.info(f"used facts: {len(used_facts)}")
        
    
    def _compress_facts_repr(self, used_facts):
        """
        Compresses fact representations by mapping facts to bit positions and converting
        states to integer representations.
        """
        # map facts to bit position for bit representation
        self._map_explicit_to_int(used_facts)
        
        # convert initial and goal state to int
        si_bitwise_repr = self._convert_to_bitwise(self.initial_state)
        sf_bitwise_repr = self._convert_to_bitwise(self.goals)
        self.initial_state = si_bitwise_repr
        self.goals = sf_bitwise_repr
        
        # convert preconditions and effects to integers for bitwise operations
        for o in self.operators:
            o.pos_precons_bitwise = self._convert_to_bitwise(o.pos_precons)
            o.neg_precons_bitwise = self._convert_to_bitwise(o.neg_precons)
            o.add_effects_bitwise = self._convert_to_bitwise(o.add_effects)
            o.del_effects_bitwise = self._convert_to_bitwise(o.del_effects)
            o.pos_precons = frozenset()
            o.neg_precons = frozenset()
            o.add_effects = frozenset()
            o.del_effects = frozenset()
        for d in self.decompositions:
            d.pos_precons_bitwise = self._convert_to_bitwise(d.pos_precons)
            d.neg_precons_bitwise = self._convert_to_bitwise(d.neg_precons)
            d.pos_precons = frozenset()
            d.neg_precons = frozenset()
            
    def _map_explicit_to_int(self, used_facts):
        """
        Maps each fact to a unique integer, creating a mapping for bitwise operations.
        This method is part of the process to convert states and operations to a bitwise format.
        """
        cont = 0
        for f in used_facts:
            self._explicit_to_int[f] = cont
            self._int_to_explicit[cont] = f
            cont+=1
    
    def _convert_to_bitwise(self, facts_set):
        bitwise_representation = 0
        for fact in facts_set:
            bit_position = self._explicit_to_int[fact]
            bitwise_representation |= 1 << bit_position
        return bitwise_representation

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
