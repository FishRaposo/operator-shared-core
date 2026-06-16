"""Regression test: the advertised `make demo` must run offline, dependency-free.

The demo previously crashed with ``ModuleNotFoundError: psycopg`` because it built a
``DatabaseManager`` from the default ``postgresql+psycopg`` URL (the engine is created
eagerly). It now defaults to an in-memory SQLite URL so it runs without psycopg.
"""

import os
import subprocess
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parents[1] / "examples" / "run_demo.py"


def test_demo_runs_offline_exit_zero():
    # Ensure no DATABASE_URL override leaks in from the environment so we exercise
    # the dependency-free SQLite default path.
    env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}

    result = subprocess.run(
        [sys.executable, str(DEMO)],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"demo exited {result.returncode}\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    output = result.stdout + result.stderr
    # No eager psycopg import should crash the demo.
    assert "ModuleNotFoundError" not in output
    assert "psycopg" not in output
    # The demo must use the dependency-free SQLite default and finish cleanly.
    assert "sqlite:///:memory:" in output
    assert "Demonstration Finished successfully" in output
