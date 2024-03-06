from Internal_Representation.precondition import Precondition
from Internal_Representation.modifier import Modifier
from Internal_Representation.action import Action
from Internal_Representation.method import Method
from Internal_Representation.predicate import Predicate
from Internal_Representation.task import Task
from Internal_Representation.Type import Type
from Internal_Representation.Object import Object
from Parsers.parser import Parser
from Internal_Representation.reg_parameter import RegParameter
from Internal_Representation.effects import Effects
from Internal_Representation.subtasks import Subtask
from Internal_Representation.problem_predicate import ProblemPredicate


class HDDLParser(Parser):
    def __init__(self, domain, problem):
        super().__init__(domain, problem)

    def parse_domain(self, domain_path):
        self.domain_path = domain_path
        tokens = self._scan_tokens(domain_path)
        if type(tokens) is list and tokens.pop(0) == 'define':
            while tokens:
                group = tokens.pop(0)
                lead = group.pop(0)

                if lead == ":action":
                    action = self._parse_action(group)
                    self.domain.add_action(action)
                elif lead == ":method":
                    method = self._parse_method(group)
                    self.domain.add_method(method)
                elif lead == ":task":
                    task = self._parse_task(group)
                    self.domain.add_task(task)
                elif lead == "domain":
                    self.domain_name = group[0]
                elif lead == ":requirements":
                    self.requirements = group
                elif lead == ":predicates":
                    self._parse_predicates(group)
                elif lead == ":types":
                    self._parse_type(group)
                elif lead == ":constraints":
                    self._parse_constraint(group)
                elif lead == ":constants":
                    self._parse_constant(group)
                else:
                    raise AttributeError("Unknown tag; {}".format(lead))
        self._post_domain_parsing_grounding()

    def parse_problem(self, problem_path):
        self.problem_path = problem_path
        tokens = self._scan_tokens(problem_path)
        if type(tokens) is list and tokens.pop(0) == 'define':
            while tokens:
                group = tokens.pop(0)
                lead = group.pop(0)

                if lead == "problem":
                    self._set_problem_name(group)
                elif lead == ":domain":
                    self._check_domain_name(group)
                elif lead == ":objects":
                    self._parse_objects(group)
                elif lead == ":init":
                    self._parse_initial_state(group)
                elif lead == ":goal":
                    self._parse_goal_state(group)
                elif lead == ":htn":
                    self._parse_htn_tag(group)
        self._post_problem_parsing_grounding()

    """Methods for parsing domains"""

    def _parse_type(self, params):
        def _add_types_to_domain(t=None):
            for o in new_types:
                self.domain.add_type(Type(o, t))

        i = 0
        l = len(params)
        new_types = []
        while i < l:
            if params[i] != "-":
                new_types.append(params[i])
                i += 1
            else:
                parent_type = self.domain.get_type(params[i + 1])

                if parent_type is False:
                    self.domain.add_type(Type(params[i + 1]))
                    parent_type = self.domain.get_type(params[i + 1])

                _add_types_to_domain(parent_type)
                new_types = []
                i += 2
        _add_types_to_domain()

    def _parse_predicates(self, params):
        for i in params:
            predicate_name = i[0]
            if len(i) > 1:
                parameter_list = self._parse_parameters(i[1:])
                self.domain.add_predicate(Predicate(predicate_name, parameter_list))
            else:
                self.domain.add_predicate(Predicate(i[0]))

    def _parse_action(self, params):
        i = 0
        l = len(params)
        action_name, parameters, precon, precon_conditions, effects = None, None, None, None, None
        while i < l:
            if i == 0:
                action_name = params[i]
            elif params[i] == ":parameters":
                parameters = self._parse_parameters(params[i + 1])
                i += 1
            elif params[i] == ":precondition":
                precon_conditions = params[i + 1]
                i += 1
            elif params[i] == ":effect":
                effects = self._parse_effects(params[i + 1])
                i += 1
            else:
                raise TypeError("Unknown identifier {}".format(params[i]))
            i += 1
        action = Action(action_name, parameters, precon, effects)
        if precon_conditions is not None:
            precon = self._parse_precondition(precon_conditions, parameters, action)
            action.add_preconditions(precon)
        return action

    def _parse_effects(self, params):
        def __extract_effect_values(params):
            if len(params) > 1:
                return params[0], params[1:]
            return params[0], []

        i = 0
        l = len(params)
        effects = Effects()
        while i < l:
            negated, predicate_name, parameters = False, None, []
            if params[i] == "and":
                return self._parse_effects(params[1:])
            elif type(params[i]) == str and params[i] != "not":
                predicate_name, parameters = __extract_effect_values(params)
                i += len(params)
            elif type(params[i]) == list:
                # [['not', ['at', '?x', '?y']], ['at', '?x', '?z']]
                if params[i][0] == "not":
                    negated = True
                    assert len(params[i]) == 2 and type(params[i][1]) == list
                    predicate_name, parameters = __extract_effect_values(params[i][1])
                else:
                    for v in params[i]:
                        assert type(v) == str
                    predicate_name, parameters = __extract_effect_values(params[i])
            else:
                # ['not', ['have', '?a']]
                if params[i] == "not":
                    negated = True
                    assert type(params[i + 1]) == list
                    predicate_name, parameters = __extract_effect_values(params[i + 1])
                    i += 1
                else:
                    predicate_name, parameters = __extract_effect_values(params[i])

            predicate = self.domain.get_predicate(predicate_name)
            effects.add_effect(predicate, parameters, negated)
            i += 1
        return effects

    def _parse_task(self, params):
        """Returns  : Task"""
        i = 0
        l = len(params)
        task_name, parameters = None, []
        while i < l:
            if i == 0:
                task_name = params[i]
            elif params[i] == ":parameters":
                assert i + 1 < l
                parameters = self._parse_parameters(params[i + 1])
                i += 1
            else:
                raise TypeError
            i += 1
        return Task(task_name, parameters)

    def _parse_method(self, params):
        i = 0
        l = len(params)
        method_name, parameters, precon, precon_conditions, task, subtasks, constraints = None, None, None, None, None, \
            None, None

        unordered_subtasks = False

        while i < l:
            if i == 0:
                if type(params[i]) != str or params[i][0] == ":":
                    raise SyntaxError("Error with Method name. Must be a string not beginning with ':'."
                                      "\nPlease check your domain file.")
                method_name = params[i]
            elif params[i] == ":parameters":
                parameters = self._parse_parameters(params[i + 1])
                i += 1
            elif params[i] == ":precondition":
                precon_conditions = params[i + 1]
                i += 1
            elif params[i] == ":constraints":
                constraints = self._parse_precondition(params[i + 1], parameters)
                i += 1
            elif params[i] == ":task":
                task_name = params[i + 1][0]
                if task is not None:
                    # Task has already been set
                    raise AttributeError("Attribute 'Task' has Already been set for the Method {}. "
                                         "Please check your domain file.".format(task_name))

                task_ob = self.domain.get_task(task_name)
                if task_ob is None:
                    raise KeyError("Task '{}' is not defined. Please check your domain file.".format(task_name))
                elif len(params[i + 1]) == 1:
                    task = {"task": task_ob, "params": []}
                else:
                    task = {"task": task_ob, "params": self._parse_parameters(params[i + 1][1:])}
                i += 1
            elif params[i] == ":ordered-subtasks" or params[i] == ":ordered-tasks":
                subtasks = self._parse_subtasks(params[i + 1])
                i += 1
            elif params[i] == ":subtasks" or params[i] == ":tasks":
                subtasks = self._parse_subtasks(params[i + 1], False)
                unordered_subtasks = True
                i += 1
            elif params[i] == ":ordering":
                assert not subtasks is None
                subtasks.order_subtasks(params[i + 1])
                i += 1
            else:
                raise SyntaxError("Unknown token {}".format(params[i]))
            i += 1

        if subtasks is not None and unordered_subtasks and len(subtasks.task_orderings) == 0:
            l = []
            for subt in subtasks.tasks:
                l.append(subt)
            subtasks.task_orderings.append(l)

        method = Method(method_name, parameters, precon, task, subtasks, constraints)
        if precon_conditions is not None:
            precon = self._parse_precondition(precon_conditions, parameters, method)
            method.add_preconditions(precon)
        return method

    def _parse_precondition(self, params, modifier_parameters, mod: Modifier = None) -> Precondition:
        def __parse_conditions(parameters, parent=None):
            if type(parameters) == list and len(parameters) == 1 and type(parameters[0]) == list:
                parameters = parameters[0]

            if type(parameters) == list:
                i = 0
                l = len(parameters)
                while i < l:
                    p = parameters[i]
                    if type(p) == str:
                        if p == "and" or p == "or" or p == "not":
                            cons = constraints.add_operator_condition(p, parent)
                            __parse_conditions(parameters[i + 1:], cons)
                            return
                        elif p == "=":
                            cons = constraints.add_operator_condition(p, parent)
                            for v in parameters[i + 1:]:
                                __parse_conditions(v, cons)
                            return
                        elif len(parameters) > 1 and all([type(x) == str for x in parameters]):
                            # Here a type is given
                            # ['valuableorhazardous', '?collect_fees_instance_2_argument_0']
                            pred = self.domain.get_predicate(p)
                            if pred is None:
                                self.domain.add_predicate(Predicate(p, self._parse_parameters(parameters[1:])))
                                pred = self.domain.get_predicate(p)

                            pred_parameters = parameters[1:]
                            """Check if all of the parameters defined in pred_parameters are given from the task
                            (assuming we are parsing a methods precondition)"""
                            if given_params is None:
                                constraints.add_predicate_condition(pred, pred_parameters, parent)
                            else:
                                # Check if all predicate_params are in given_params
                                if all([x in given_params for x in pred_parameters]):
                                    if parent is None:
                                        constraints.add_given_params_predicate_condition(pred, pred_parameters,
                                                                                         parent)
                                    elif parent.operator == "not":
                                        parent2 = parent.parent
                                        if parent2 is not None:
                                            parent2.children.remove(parent)
                                        else:
                                            constraints.head = None

                                        operator_parent = constraints.add_given_params_operator_condition("not")
                                        constraints.add_given_params_predicate_condition(pred, pred_parameters,
                                                                                         operator_parent)
                                        parent = parent.parent
                                    else:
                                        constraints.add_given_params_predicate_condition(pred, pred_parameters, parent)
                                else:
                                    constraints.add_predicate_condition(pred, pred_parameters, parent)
                            i = l
                        elif len(parameters) == 1 and type(p) == str:
                            constraints.add_predicate_condition(self.domain.get_predicate(p), [], parent)
                            i = l
                        elif p == "forall":
                            if len(parameters) == 3:
                                selector = parameters[1]
                                satisfier = self._parse_precondition(parameters[2], modifier_parameters)
                            else:
                                selector = parameters[1] + [self._parse_precondition(['and'] + parameters[2])]
                                satisfier = self._parse_precondition(['and'] + parameters[3])
                            constraints.add_forall_condition(selector, satisfier.head, parent)
                            i += l
                        else:
                            raise TypeError("Unexpected token {}".format(p))
                    elif type(p) == list:
                        __parse_conditions(p, parent)
                    else:
                        raise TypeError("Unexpected type {}".format(type(p)))
                    i += 1
            elif type(parameters) == str:
                if parameters in modifier_parameters:  # TODO: Fix this, this refers to the parameters passed from a task to a method not any parameters
                    # This means we have a constraint on a parameter passed to the modifier
                    return constraints.add_variable_condition(parameters, parent)
                # This means we care about the value of an object
                return constraints.add_constant_object_condition(parameters, parent, self.problem)
            else:
                raise TypeError("Unexpected type {}".format(type(parameters)))

        constraints = Precondition(params)
        if type(mod) == Method:
            given_params = [x.name for x in mod.task['params']]
        else:
            given_params = None
        given_mod = mod
        if not all([type(n) == str for n in modifier_parameters]):
            modifier_parameters = [p.name for p in modifier_parameters]
        __parse_conditions(params)
        return constraints

    def _parse_constant(self, params):
        def __add_constants_to_problem(t=None):
            for c in new_constants:
                constant_object = Object(c, t)
                self.problem.add_object(constant_object)
                self.domain.add_constant(Object(c, t))

        i = 0
        l = len(params)
        new_constants = []
        while i < l:
            v = params[i]
            if v == "-":
                v = params[i + 1]
                const_type = self.domain.get_type(v)
                if const_type is None or const_type == False:
                    raise TypeError(
                        "Type {} not found when parsing constants. Please check your domain file.".format(v))
                __add_constants_to_problem(const_type)
                new_constants = []
                i += 1
            else:
                new_constants.append(v)
            i += 1
        __add_constants_to_problem()
        new_constants = []

    def _post_domain_parsing_grounding(self):
        for item in self._requires_grounding:
            if type(item) == Subtask:
                # Make sure item.task is a modifier and not a string
                if type(item.task) != Modifier and type(item.task) == str:
                    retrieved = self.domain.get_modifier(item.task)
                    if not isinstance(retrieved, Modifier):
                        raise TypeError("No valid modifier found for {}".format(item.task))
                    item.task = retrieved
        self._requires_grounding = []

    """Methods for parsing problems"""

    def _set_problem_name(self, params):
        if type(params) == list and len(params) == 1 and type(params[0]) == str:
            params = params[0]
        elif type(params) == str:
            pass
        else:
            raise TypeError("Given value must be a string or a list with one string inside. Given {}".format(params))
        assert type(params) == str
        self.problem.set_name(params)

    def _check_domain_name(self, name):
        """Returns True - if param: name is equal to self.domain_name"""
        if type(name) == list:
            name = name[0]
        if name == self.domain_name:
            return True
        else:
            raise NameError("Domain specified in problem file {} ({}). Does not match domain specified in {} ({})"
                            .format(self.problem_path, name, self.domain_path, self.domain_name))

    def _parse_objects(self, params):
        def _add_objects_to_problem(t=None):
            for o in new_obs:
                self.problem.add_object(Object(o, t))

        i = 0
        l = len(params)
        new_obs = []
        while i < l:
            if params[i] != "-":
                new_obs.append(params[i])
                i += 1
            else:
                obs_type = self.domain.get_type(params[i + 1])
                _add_objects_to_problem(obs_type)
                new_obs = []
                i += 2
        _add_objects_to_problem()

    def _parse_initial_state(self, params):
        for i in params:
            # Create ProblemPredicate
            obs = [self.problem.get_object(x) for x in i[1:]]
            self.problem.add_to_initial_state(ProblemPredicate(self.domain.get_predicate(i[0]), obs))

    def _parse_htn_tag(self, params):
        ordered_subtasks = False
        ordered = False

        while params:
            lead = params.pop(0)

            if lead == ":ordered-subtasks" or lead == ":ordered-tasks":
                subtasks = self._parse_subtasks(params.pop(0))
                self.problem.add_subtasks(subtasks)
                self._requires_grounding.append(subtasks)
                ordered_subtasks = True
            elif lead == ":tasks" or lead == ":subtasks":
                subtasks = self._parse_subtasks(params.pop(0), False)
                self.problem.add_subtasks(subtasks)
                self._requires_grounding.append(subtasks)
            elif lead == ":parameters":
                group = params.pop(0)
                if group != []:
                    while group:
                        param_name = group.pop(0)
                        group.pop(0)  # This is the '-' between the parameter name and type
                        param_type_str = group.pop(0)
                        self.problem.add_initial_task_network_parameter(param_name, param_type_str)
            elif lead == ":ordering":
                self.problem.set_initial_subtask_ordering(params.pop(0))
                ordered = True
            elif lead == ":constraints":
                group = params.pop(0)
                if len(group) > 0:
                    raise NotImplementedError("Constraints on Problem Initiation is not supported")
            else:
                raise TypeError("Unknown keyword {}".format(lead))

        if not ordered_subtasks and not ordered:
            # We need to order the subtasks
            self.problem.set_initial_subtask_ordering([])
            self.problem.order_subtasks()

    def _parse_goal_state(self, params):
        if type(params) == list and len(params) == 1 and type(params[0]) == list and len(params[0]) > 1:
            params = params[0]
        cons = self._parse_precondition(params, [])
        self.problem.add_goal_conditions(cons)

    def _scan_tokens(self, file_path):
        return super(HDDLParser, self)._scan_tokens(file_path)
