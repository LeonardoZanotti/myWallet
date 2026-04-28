import os
import subprocess
import sys


def test_frontend_behaviors():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    script_path = os.path.join(project_root, 'tests', 'frontend.spec.js')

    result = subprocess.run(
        ['node', script_path],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, result.stdout + result.stderr
