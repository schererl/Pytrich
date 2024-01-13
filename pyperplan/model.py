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
    The preconditions represent the facts that have to be true
    before the operator can be applied.
    add_effects are the facts that the operator makes true.
    delete_effects are the facts that the operator makes false.
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

    def applicable_bitwise(self, state_bitwise):
        return ((state_bitwise & self.pos_precons_bitwise) == self.pos_precons_bitwise) and \
               ((state_bitwise & self.neg_precons_bitwise) == 0)

    
    def apply_bitwise(self, state_bitwise):
        return (state_bitwise & ~self.del_effects_bitwise) | self.add_effects_bitwise

    
    def applicable(self, state):
        return self.pos_precons <= state and self.neg_precons.isdisjoint(state)
        
    def apply(self, state):
        return (state - self.del_effects) | self.add_effects

    def __eq__(self, other):
        return (
            self.name == other.name
        )

    def __hash__(self):
        return  self.hash_name

    def __str__(self):
        s = "%s " % self.name
        #s+= "pre: %s" % self.preconditions
        for add_eff in self.pos_precons:
            s += f"{add_eff} "
        for del_eff in self.neg_precons:
            s += f"not{del_eff} "
        s+= "  eff: "
        for add_eff in self.add_effects:
            s += f"{add_eff} "
        for del_eff in self.del_effects:
            s += f"not{del_eff} "
        
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
        for pos_pre in self.pos_precons:
            s += f"{pos_pre} "
        for neg_pre in self.neg_precons:
            s += f"not{neg_pre} "
        
        s += f"  Decomposed Task: {self.decomposed_task}\n"
        s += f"  Task Network: {self.task_network[0:min(5, len(self.task_network))]}\n"
        return s
    
    
## GOAL COUNT HEURISTICS ##
# NOTE: maybe here we compute the heuristic value for the operators and decompositions before start the searching

class Model:
    """
    A STRIPS planning task
    """

    def __init__(self, name, facts, initial_state, goals, operators, initial_tn, decompositions):
        """
        Initializes a planning model with its properties.
        @param name: The name of the planning task.
        @param facts: A set of all fact names in the domain.
        @param initial_state: The initial state of the planning task.
        @param goals: The goal state(s) of the planning task.
        @param operators: A set of operator instances for the domain.
        @param initial_tn: The initial task network for HTN planning.
        @param decompositions: A set of decomposition instances for HTN planning.
        """
        self.name = name
        self.facts = facts
        self.initial_state = initial_state
        self.goals = goals
        self.operators = operators
        self.initial_tn = initial_tn
        self.decompositions = decompositions
        self.states = {}
        
        # goal count control
        self.count_goal_facts = len(self.goals)
        self.count_goal_tasks = len(self.initial_tn)
        
        # model optimizations 
        self._explicit_to_int = {}
        self._int_to_explicit = {}
        self._compress_model_repr()
        
        self._process_goal_task_count() #NOTE: before converting into bit representation, add task counts into grounded tasks
        self._process_goal_facts_count() #NOTE: before converting into bit representation, add facts counts into operators

        self._compress_facts_repr(self.facts) #NOTE: won't work without compress_model (facts are empty before it)

    def _process_goal_facts_count():
        pass
    def _process_goal_task_count():
        pass    
        
    def goal_reached(self, state, task_network=[]):
        """
        The goal has been reached if all facts that are true in "goals"
        are true in "state".

        @return True if all the goals are reached, False otherwise
        """
        if isinstance(state, int) and isinstance(self.goals, int):
            return (state & self.goals) == self.goals and len(task_network) == 0
        else:
            return self.goals <= state and len(task_network) == 0

    def methods(self, task):
        return task.decompositions 

    def decompose(self, decomposition):
        return decomposition.task_network
    
     
    def apply(self, operator, state):
        if isinstance(state, int):
            return operator.apply_bitwise(state)
        else:
            return operator.apply(state)
    
    
    def applicable(self, modifier, state):
        if isinstance(state, int):
            return modifier.applicable_bitwise(state)
        else:
            return modifier.applicable(state)

    ### OPTIMIZING MODEL ### 
    def _compress_model_repr(self):
        """
        Compresses the model representation to optimize memory usage and performance.

        It filters out unused operators and decompositions based on the initial task network,
        and updates the model with only the necessary elements.
        It also logs the memory usage before and after the compression for profiling purposes.

        NOTE: Less eficient than rechability analysis -it doesnt consider preconditions
        """
        used_operators = []
        used_decompositions = []
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
                for method in self.methods(task):
                    used_decompositions.append(method)
                    used_facts.update(method.pos_precons)
                    used_facts.update(method.neg_precons)
                    tasks+= self.decompose(method)[:]

        # profilling stuff
        op_before = sys.getsizeof(self.operators) 
        decomp_before = sys.getsizeof(self.decompositions) 
        self.operators = used_operators
        self.decompositions = used_decompositions
        self.facts = used_facts
        op_after = sys.getsizeof(self.operators) 
        decomp_after = sys.getsizeof(self.decompositions) 
        logging.info(f"cleaning operators: before {op_before} bytes ==> after {op_after} bytes")
        logging.info(f"cleaning decompositions: before {decomp_before} bytes ==> after {decomp_after} bytes")
        logging.info(f"used facts: {len(used_facts)}")
        
        
        
    
    def _compress_facts_repr(self, used_facts):
        """
        Compresses fact representations by mapping facts to bit positions and converting
        states to bitwise representations.
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
            o.pos_precons = None
            o.neg_precons = None
            o.add_effects = None
            o.del_effects = None
        for d in self.decompositions:
            d.pos_precons_bitwise = self._convert_to_bitwise(d.pos_precons)
            d.neg_precons_bitwise = self._convert_to_bitwise(d.neg_precons)
            d.pos_precons = None
            d.neg_precons = None
            
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
