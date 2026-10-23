"""Opt-in request budget for explicitly bounded independent policy retries."""
import ast


def is_observation_only(source):
    """Conservatively prove every possible call is read-only, otherwise count it."""
    tree = ast.parse(source)
    pure = {'get_task_context', 'get_observation', 'get_robot_state', 'segment_text',
            'segment_points', 'mask_to_point_cloud', 'crop_point_cloud', 'estimate_geometry',
            'localize_object', 'generate_grasps', 'select_grasp', 'solve_ik', 'plan_motion',
            'Pose', 'MotionStrategy', 'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
            'float', 'int', 'len', 'list', 'max', 'min', 'range', 'round', 'sorted',
            'str', 'sum', 'tuple', 'zip', 'print'}
    action_names = {'step', 'execute_trajectory', 'move_to_joints', 'move_to_pose',
                    'go_home', 'open_gripper', 'close_gripper', 'set_gripper',
                    'set_grippers', 'move_synchronized', 'execute_synchronized_trajectory'}
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    containers = set()
    unsafe = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            literal_container = isinstance(node.value, (ast.List, ast.Dict, ast.ListComp, ast.DictComp))
            for target in node.targets:
                if isinstance(target, ast.Name):
                    (containers if literal_container else unsafe).add(target.id)
    containers -= unsafe
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if not isinstance(node, ast.Import) or any(a.name != 'math' or a.asname for a in node.names):
                return False
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in action_names or node.func.id not in pure | functions:
                    return False
            elif isinstance(node.func, ast.Attribute):
                receiver = node.func.value
                if node.func.attr in {'append', 'extend'}:
                    while isinstance(receiver, ast.Subscript):
                        receiver = receiver.value
                    if isinstance(receiver, ast.Name) and receiver.id in containers:
                        continue
                owner = node.func.value.id if isinstance(node.func.value, ast.Name) else None
                if owner == 'math' and not node.func.attr.startswith('_'):
                    continue
                if owner in {'libero', 'robosuite'} and node.func.attr in {'get_task_metadata', 'get_controller_metadata'}:
                    continue
                return False
            else:
                return False
    return True


def check_budget(history, request, source_hash, max_versions, max_per_mode=3):
    """Validate against finalized requests without counting repeated source sweeps."""
    assert max_versions > 0
    mode = request.get('failure_mode')
    assert isinstance(mode, str) and mode.strip(), 'failure_mode is required for bounded retry'
    sources = {}
    for record in history:
        prior_hash = record['source_hash']
        if record.get('observation_only'):
            continue
        prior_mode = record.get('failure_mode')
        assert isinstance(prior_mode, str) and prior_mode, 'Prior bounded request lacks failure_mode'
        sources.setdefault(prior_hash, prior_mode)
        if record['program'] == request['program']:
            assert prior_hash == source_hash, 'Numbered source changed in place; write a new version'
    if source_hash in sources:
        assert sources[source_hash] == mode, 'A source cannot be relabeled to reset a mode budget'
        return
    if request.get('observation_only'):
        return
    assert len(sources) < max_versions, f'Policy version budget exhausted ({max_versions})'
    used_mode = sum(prior_mode == mode for prior_mode in sources.values())
    assert used_mode < max_per_mode, f'Failure mode budget exhausted: {mode} ({max_per_mode})'
