from pychronicle.cli import _build_trace_steps, _render_timeline

if __name__ == '__main__':
    steps = _build_trace_steps('tests/sample_script.py')
    if not steps:
        print('No steps recorded')
    else:
        _render_timeline(steps, len(steps) - 1, 'tests/sample_script.py')
