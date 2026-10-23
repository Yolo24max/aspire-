"""Keep independent retry validation and transfer identities out of original trees."""
import re


def attempt_layout(base_task, attempt_name=None):
    if attempt_name is None:
        return base_task, '', base_task / 'validation' / 'runs'
    if not re.fullmatch(r'(retry|rerun)_[0-9]{2,}', attempt_name):
        raise ValueError('Attempt name must be a single retry_NN or rerun_NN component')
    task = base_task / attempt_name
    # Explicit run_validation --output-root retains benchmark/task nesting.
    runs = task / 'validation' / 'libero-pro' / 'libero_goal_swap' / base_task.name / 'runs'
    return task, '-' + attempt_name, runs
