from pyperplan.parser.hddl import Domain, Problem, Precondition, Predicate, AbstractTask, Action, Method, Effect, Type

BLOCKSWORLD_PREDICATE_LIST =  [
    ':predicates', 
    ['on', '?x', '-', 'block', '?y', '-', 'block'], 
    ['ontable', '?x', '-', 'block'], 
    ['clear', '?x', '-', 'block'], 
    ['handempty'], 
    ['holding', '?x', '-', 'block']
]

BLOCKSWORLD_TYPE_LIST = [':types', 'block', 'circle'] 

BLOCKSWORLD_ACTION_LIST = {
    'stack':
    [
        ':action', 'stack',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'block'],
        ':precondition', ['and', ['holding', '?x'], ['clear', '?y']],
        ':effect', ['and', ['not', ['holding', '?x']], ['not', ['clear', '?y']], ['clear', '?x'], ['handempty'], ['on', '?x', '?y']]
    ], 
    'unstack':
    [
        ':action', 'unstack',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'block'],
        ':precondition', ['and', ['on', '?x', '?y'], ['clear', '?x'], ['handempty']],
        ':effect', ['and', ['holding', '?x'], ['clear', '?y'], ['not', ['clear', '?x']], ['not', ['handempty']], ['not', ['on', '?x', '?y']]]
    ],
    'noop': 
    [
        ':action', 'noop',
        ':parameters', [],
        ':precondition', [],
        ':effect', []
    ]
}

BLOCKSWORLD_TASK_LIST = {
    'do_on_table' : [':task', 'do_on_table',':parameters', ['?x', '-', 'block']], 
    'do_move' : [':task', 'do_move',':parameters', ['?x', '-', 'block', '?y', '-', 'block']]
}

BLOCKSWORLD_METHOD_LIST = {
    'm5_do_move': 
    [
        ':method', 'm5_do_move',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'block', '?z', '-', 'block'],
        ':task', ['do_move', '?x', '?y'],
        ':precondition', ['and', ['clear', '?x'], ['clear', '?y'], ['handempty'], ['not', ['ontable', '?x']]],
        ':ordered-subtasks', ['and', ['t1', ['unstack', '?x', '?z']], ['t2', ['stack', '?x', '?y']]]
    ]
}

DUMMY_ACTION_LIST = {
    'still_valid_action' : 
    [
        ':action', 'still_valid_action',
        ':parameters', ['?k','-','block'],
        ':precondition', ['clear', '?k'],
        ':effect', []
    ],
    'invalid_action' : 
    [
        ':action', 'invalid_action'
        ':parameters', ['?x','-','block','?y','-','circle'],
        ':precondition', ['and', ['holding', '?x'], ['clear', '?y']],
        ':effect', ['and', ['not', ['holding', '?x']], ['not', ['clear', '?y']], ['clear', '?x'], ['handempty'], ['on', '?x', '?y']]
    ]
}

DUMMY_METHOD_LIST = {
    'invalid_task_method' : 
    [
        ':method', 'invalid_task_method',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'circle', '?z', '-', 'block'],
        ':task', ['do_move', '?x', '?y'],
        ':precondition', ['and', ['clear', '?x']],
        ':ordered-subtasks', ['and', ['t1', ['stack', '?x', '?z']]]
    ],
    'invalid_precondition_method' : 
    [
        ':method', 'invalid_precondition_method',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'circle', '?z', '-', 'block'],
        ':task', ['do_move', '?x', '?z'],
        ':precondition', ['and', ['clear', '?y']],
        ':ordered-subtasks', ['and', ['t1', ['stack', '?x', '?z']]]
    ],
    'invalid_subtask_method' : 
    [
        ':method', 'invalid_subtask_method',
        ':parameters', ['?x', '-', 'block', '?y', '-', 'circle', '?z', '-', 'block'],
        ':task', ['do_move', '?x', '?z'],
        ':precondition', ['and', ['clear', '?x']],
        ':ordered-subtasks', ['and', ['t1', ['stack', '?x', '?y']]]
    ],
    'still_valid_method' : 
    [
        ':method', 'still_valid_method',
        ':parameters', ['?k', '-', 'block'],
        ':task', ['do_on_table', '?k'],
        ':precondition', ['clear', '?k'],
        ':ordered-subtasks', ['and', ['t1', ['nop']]]
    ]
}

BARMAN_TYPES_LIST = [':types', 'anything', '-', 'object', 'container', 'dispenser', 'level', 'beverage', 'hand', '-', 'anything', 'shot', 'shaker', '-', 'container', 'ingredient', 'cocktail', '-', 'beverage']

def instance_blocksworld_abstract_tasks():
    # assuming we already parsed :types from domain
    types = instance_blockworld_domain_types()
    # instance do on table
    task_name = 'do_on_table'
    task_signature = [('?x', types['block'])]
    task_do_on_table = AbstractTask(task_name, task_signature)

    # instance do move
    task_name = 'do_move'
    task_signature = [('?x', types['block']), ('?y', types['block'])]
    task_do_move = AbstractTask(task_name, task_signature)
    
    return {'do_on_table':task_do_on_table, 'do_move':task_do_move}

def instance_blockworld_domain_types():
    from pyperplan.parser.hddl import Type
    object_type = Type('object', None)
    block_type = Type('block', object_type)
    circle_type = Type('circle', object_type)
    types = {'block': block_type, 'circle': circle_type}
    return types

def instance_barman_bdi_domain_types():
    from pyperplan.parser.hddl import Type

    [':types', 
     'anything', '-', 'object', 
     'container', 'dispenser', 'level', 'beverage', 'hand', '-', 'anything', 
     'shot', 'shaker', '-', 'container', 
     'ingredient', 'cocktail', '-', 'beverage'
    ]

    object_type    = Type('object', None)
    anything_type  = Type('anything', object_type)
    container_type = Type('container', anything_type)
    dispenser_type = Type('dispenser', anything_type)
    level_type     = Type('level', anything_type)
    beverage_type  = Type('beverage', anything_type)
    hand_type      = Type('hand', anything_type)
    shot_type      = Type('shot', container_type)
    shaker_type    = Type('shaker', container_type)
    ingredient_type = Type('ingredient', beverage_type)
    cocktail_type   = Type('cocktail', beverage_type)

    types = {
        'object': object_type,
        'anything': anything_type,
        'container': container_type,
        'dispenser': dispenser_type,
        'level': level_type,
        'beverage': beverage_type,
        'hand': hand_type,
        'shot': shot_type,
        'shaker': shaker_type,
        'ingredient': ingredient_type,
        'cocktail': cocktail_type
    }
    return types

def instance_blocksworld_domain_actions():
    types = instance_blockworld_domain_types()
    action_name = 'stack'
    action_signature = [('?x', types['block']), ('?y', types['block'])]
    
    pholding = Predicate('holding', [('?x', types['block'])])
    pclear_y = Predicate('clear', [('?y', types['block'])])
    pon = Predicate('on', [('?x', types['block']), ('?y', types['block'])])
    phandempty = Predicate('handempty', [])
    pclear_x = Predicate('clear', [('?x', types['block'])])

    positive_preconditions = {pholding, pclear_y}
    negative_preconditions = set()
    preconditions = Precondition(positive_preconditions, negative_preconditions)
    add_effects = {pon, pclear_x, phandempty}
    del_effects = {pholding, pclear_y}
    effects = Effect(add_effects, del_effects)
    stack_action = Action(action_name, action_signature, preconditions, effects)

    positive_preconditions = {pon, pclear_x, phandempty}
    negative_preconditions = set()
    preconditions = Precondition(positive_preconditions, negative_preconditions)
    
    add_effects = {pholding, pclear_y}
    del_effects = {pon, pclear_x, phandempty}
    effects = Effect(add_effects, del_effects)
    
    unstack_action = Action(action_name, action_signature, preconditions, effects)

    
    noop_action = Action('noop', {}, Precondition({},{}), Effect({},{}))
    return {'stack':stack_action, 'unstack':unstack_action, 'noop':noop_action}

def instance_blocksworld_domain_predicates():
    ':predicates', 
    ['on', '?x', '-', 'block', '?y', '-', 'block'], 
    ['ontable', '?x', '-', 'block'], 
    ['clear', '?x', '-', 'block'], 
    ['handempty'], 
    ['holding', '?x', '-', 'block']
    types = instance_blockworld_domain_types()
    pclear = Predicate('clear', [('?x', types['block'])])
    pontable = Predicate('ontable', [('?x', types['block'])])
    phandempty = Predicate('handempty', [])
    pholding = Predicate('holding', [('?x', types['block'])])
    pon = Predicate('on', [('?x', types['block']), ('?y', types['block'])])
    return {
        'clear': pclear,
        'ontable': pontable,
        'handempty': phandempty,
        'holding': pholding,
        'on': pon
    }

def test_parse_types():
    from pyperplan.parser.parser import Parser
    parser = Parser()
    parsed_types   = parser.parse_types(BLOCKSWORLD_TYPE_LIST[1:])
    instaced_types = instance_blockworld_domain_types()

    for type_name in BLOCKSWORLD_TYPE_LIST[1:]:
        assert parsed_types[type_name]
        assert instaced_types[type_name] == parsed_types[type_name]

    # a little harder type assertion
    harder_parsed_types    = parser.parse_types(BARMAN_TYPES_LIST[1:])
    harder_instanced_types = instance_barman_bdi_domain_types()
    for token in BARMAN_TYPES_LIST[1:]:
        if token == '-':
            continue
        type_name = token
        assert harder_parsed_types[type_name]
        assert harder_parsed_types[type_name] == harder_instanced_types[type_name]

def test_parse_predicates():
    from pyperplan.parser.parser import Parser
    parser = Parser()
    parsed_predicates = parser.parse_predicates(BLOCKSWORLD_PREDICATE_LIST[1:])
    instanced_predicates = instance_blocksworld_domain_predicates()
    for predicate_group in BLOCKSWORLD_PREDICATE_LIST[1:]:
        predicate_name = predicate_group[0]
        assert parsed_predicates[predicate_name]
        assert parsed_predicates[predicate_name] == instanced_predicates[predicate_name]

def test_parse_action():
    from pyperplan.parser.parser import Parser
    parser = Parser()
    
    # assuming we already parsed :types from domain
    parser.types = instance_blockworld_domain_types()
    parser.predicates = instance_blocksworld_domain_predicates()
    
    # now lets check if the action is properly parsed
    action_instances = instance_blocksworld_domain_actions()
    action_tokens = BLOCKSWORLD_ACTION_LIST
    
    for token in action_tokens.values():   
        action_name = token[1]
        assert action_instances[action_name] == parser.parse_action(token[1:]), f"{action_instances[action_name]} == {parser.parse_action(token[1:])}"

def test_action_signature_validation():
    from pyperplan.parser.parser import IllegalParameterTypeException
    from pyperplan.parser.parser import Parser
    '''
        Ensure that the parameters and predicates of an action are accordingly with domain predicates types description.
    '''
    parser = Parser()
    # assuming we already parsed :types and :predicates from domain
    parser.types = instance_blockworld_domain_types()
    parser.predicates = instance_blocksworld_domain_predicates()
    
    # check a valid action all parameters types and predicates are accordingly domain's predicates
    actions = BLOCKSWORLD_ACTION_LIST
    stack_action = actions['stack']
    try:
        parser.parse_action(stack_action[1:])
    except IllegalParameterTypeException:
        assert False, "Action 'stack' signature validation lead to an unexpected IllegalParameterTypeException"

    dummy_actions = DUMMY_ACTION_LIST
    invalid_action = dummy_actions['invalid_action']
    
    try:
        parser.parse_action(invalid_action[1:])
        assert False, "Action 'invalid_action' Expected an IllegalParameterTypeException "
    except IllegalParameterTypeException:
        pass

    # test a valid action with different variable names respecting type signature for action predicates
    still_valid_action = dummy_actions['still_valid_action']
    try:
        parser.parse_action(still_valid_action[1:])
    except:
        assert False, "Action 'still_valid_action' unexpected exception, signature types are the same: predicate\'s signature is {clear:[(?x,block)]}, and action signature is {clear:[(?k-block)]}"


def test_parse_abstract_task():
    from pyperplan.parser.parser import Parser
    parser = Parser()
    
    # assuming we already parsed :types from domain
    parser.types = instance_blockworld_domain_types()
    parser.predicates = instance_blocksworld_domain_predicates()
    # tokens we want to parse
    tasks = BLOCKSWORLD_TASK_LIST
    
    tokens = tasks['do_on_table']
    group = tokens[1:]

    # instance abstract task
    task_name = 'do_on_table'
    task_signature = [('?x', parser.types['block'])]
    do_on_table_task = AbstractTask(task_name, task_signature)
    assert do_on_table_task == parser.parse_abstract_task(group)

def test_parse_method():
    from pyperplan.parser.parser import Parser
    from pyperplan.parser.parser import IllegalParameterTypeException
    parser = Parser()
    # get necessary structures first
    parser.types      = instance_blockworld_domain_types()
    parser.predicates = instance_blocksworld_domain_predicates()
    parser.actions    = instance_blocksworld_domain_actions()
    parser.abstract_tasks = instance_blocksworld_abstract_tasks()
    

    from pyperplan.parser.hddl import Method, Precondition, AbstractTask, Predicate
    methods = BLOCKSWORLD_METHOD_LIST
    tokens = methods['m5_do_move']
    method_group = tokens[1:]
    
    # instance method: instance Predicates, Preconditions, OrderedSubtasks
    method_name = 'm5_do_move'
    method_signature = {'?x': parser.types['block'], '?y': parser.types['block'], '?z': parser.types['block']}
    method_task_head = parser.abstract_tasks['do_move']
    # instance precondition's predicate assert they are correctly defined
    pclear_x = Predicate('clear', [('?x', method_signature['?x'])])
    pclear_y = Predicate('clear', [('?y', method_signature['?y'])])
    phandempty = Predicate('handempty', [])
    pontable = Predicate('ontable', [('?x', method_signature['?x'])])
    positive_preconditions = {pclear_x, pclear_y, phandempty}
    negative_preconditions = {pontable}
    preconditions = Precondition(positive_preconditions, negative_preconditions)

    ordered_subtasks = [
        parser.actions['unstack'],
        parser.actions['stack']
    ]
    
    method = Method(method_name, method_signature, preconditions, method_task_head, ordered_subtasks)
    assert method == parser.parse_method(method_group)
    
def test_parse_method_signature_validation():
    from pyperplan.parser.parser import IllegalParameterTypeException, Parser
    
    parser = Parser()
    # required already parsed stuff
    parser.types = instance_blockworld_domain_types()
    parser.predicates = instance_blocksworld_domain_predicates()
    parser.actions = instance_blocksworld_domain_actions()
    parser.abstract_tasks = instance_blocksworld_abstract_tasks()
    
    # validate different method situations
    methods = DUMMY_METHOD_LIST
    

    invalid_method_1 = methods['invalid_task_method']
    invalid_method_2 = methods['invalid_precondition_method']
    invalid_method_3 = methods['invalid_subtask_method']
    try:
        parser.parse_method(invalid_method_1[1:])
        assert False, "Method named 'invalid_task_method' did not raise an IllegalParameterTypeException: declared 'do_move ?x - block ?y - circle'. Domain's task signature is 'do_move ?x - block ?y - block'"
    except IllegalParameterTypeException:
        pass
    
    try:
        parser.parse_method(invalid_method_2[1:])
        assert False, "Method named 'invalid_precondition_method' did not raise an IllegalParameterTypeException: declared clear ?y-circle. Domain's proposition signature is 'clear ?x-block'"
    except IllegalParameterTypeException:
        pass
    
    try:
        parser.parse_method(invalid_method_3[1:])
        assert False, "Method named 'invalid_subtask_method' did not raise an IllegalParameterTypeException: decleared 'stack' uses '?x - block ?y - circle'. Domain's action signature is 'stack ?x - block ?y - block'."
    except IllegalParameterTypeException:
        pass

    still_valid_method = methods['still_valid_method']
    try:
        parser.parse_method(still_valid_method[1:])
    except:
        assert False, "Method named 'still_valid_method' had an unexpected exception, signature types are the same, different variable names still valid."
    
    
