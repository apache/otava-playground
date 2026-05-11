"""
Invoke tasks for otava-test-data project.

Usage:
    inv --list          # List available tasks
    inv test            # Run tests
    inv lint            # Run linter
    inv docs            # Build documentation
    inv generate        # Generate test data
"""

from invoke import task, Context
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


@task
def install(c: Context, dev: bool = True, web: bool = False):
    """Install the package and dependencies."""
    extras = ["dev", "docs"]
    if web:
        extras.append("web")

    if dev:
        c.run(f"uv pip install -e '.[{','.join(extras)}]'", pty=True)
    else:
        c.run("uv pip install -e .", pty=True)


@task
def test(c: Context, verbose: bool = False, coverage: bool = False, marker: str = ""):
    """Run the test suite."""
    cmd = "uv run pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=otava_test_data --cov-report=term-missing"

    if marker:
        cmd += f" -m '{marker}'"

    cmd += " src/otava_test_data/tests/"
    c.run(cmd, pty=True)


@task
def test_generators(c: Context):
    """Run only the generator tests (no Otava required)."""
    c.run("uv run pytest src/otava_test_data/tests/test_generators.py -v", pty=True)


@task
def test_otava(c: Context):
    """Run only the Otava integration tests."""
    c.run("uv run pytest src/otava_test_data/tests/test_otava_integration.py -v", pty=True)


@task
def lint(c: Context, fix: bool = False):
    """Run the linter (ruff)."""
    cmd = "uv run ruff check src/"
    if fix:
        cmd += " --fix"
    c.run(cmd, pty=True)


@task
def format(c: Context, check: bool = False):
    """Format code with ruff."""
    cmd = "uv run ruff format src/"
    if check:
        cmd += " --check"
    c.run(cmd, pty=True)


@task
def generate(
    c: Context,
    output_dir: str = "./test_data",
    lengths: str = "50,500",
    seed: int = 42,
):
    """Generate test data CSV files."""
    length_args = " ".join(f"-l {l}" for l in lengths.split(","))
    c.run(
        f"uv run python -m otava_test_data.cli generate "
        f"--output-dir {output_dir} {length_args} --seed {seed}",
        pty=True,
    )


@task
def docs_build(c: Context):
    """Build Sphinx documentation."""
    c.run("uv run sphinx-build -b html docs/ docs/_build/html", pty=True)


@task
def docs_serve(c: Context, port: int = 8000):
    """Serve documentation locally."""
    c.run(
        f"uv run python -m http.server {port} --directory docs/_build/html",
        pty=True,
    )


@task
def docs_init(c: Context):
    """Initialize Sphinx documentation structure."""
    docs_dir = os.path.join(PROJECT_DIR, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    # Create conf.py
    conf_content = '''"""Sphinx configuration for otava-test-data."""

project = "otava-test-data"
copyright = "2025, Joe Drumgoole"
author = "Joe Drumgoole"
version = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# MyST settings for markdown
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# Napoleon settings for docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
'''

    conf_path = os.path.join(docs_dir, "conf.py")
    with open(conf_path, "w") as f:
        f.write(conf_content)

    # Create index.md
    index_content = '''# Otava Test Data

Test data generators for Apache Otava change point detection.

## Overview

This package provides generators for creating synthetic time series data
with known change points for testing and benchmarking change point detection
algorithms.

## Installation

```bash
pip install otava-test-data
```

## Quick Start

```python
from otava_test_data import step_function, noise_normal, combine

# Generate a step function with noise
step = step_function(length=500, value_before=100, value_after=120)
noise = noise_normal(length=500, mean=0, sigma=5)
ts = combine(step, noise)

# Export to CSV for Otava
ts.to_csv("test_data.csv")

# Access change point information
for cp in ts.change_points:
    print(f"Change at index {cp.index}: {cp.description}")
```

## Contents

```{toctree}
:maxdepth: 2

generators
api
benchmark
```
'''

    index_path = os.path.join(docs_dir, "index.md")
    with open(index_path, "w") as f:
        f.write(index_content)

    # Create generators.md
    generators_content = '''# Time Series Generators

## Basic Building Blocks

These generators create fundamental time series patterns used in performance
testing scenarios.

### Constant

A constant time series: `S = x, x, x, x...`

Represents an ideal performance test with no variation.

### Noise (Normal)

Normally distributed noise: `S = x1, x2, x3...` where `X ~ N(mean, sigma)`

Represents typical performance test output with random variation.

### Noise (Uniform)

Uniformly distributed noise (white noise): `random(min, max)`

### Outlier

Single deviating point (anomaly): `S = x, x, x, x, x, x', x, x...`

### Step Function

Single change point: `S = x1, x1, x1, x2, x2, x2...`

Represents a performance regression or improvement that persists.

### Regression + Fix

Temporary regression: `S = x1, x1... x2, ...x2, x3, x3...`

## Advanced Phenomena

### Banding

Oscillation between two values: `S = x1, x2, x2, x1, x2, x1...`

### Variance Change

Constant mean, changing variance: `S = N(mean, sigma1)..., N(mean, sigma2)...`

### Phase Change

Constant mean and variance, but phase shifts: `S = cos(x)..., sin(x)...`

### Multiple Changes

Multiple consecutive changes: `S = x0, x0... x1, x2, ... xn, xn...`
'''

    gen_path = os.path.join(docs_dir, "generators.md")
    with open(gen_path, "w") as f:
        f.write(generators_content)

    # Create api.md
    api_content = '''# API Reference

```{eval-rst}
.. automodule:: otava_test_data
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: otava_test_data.generators.basic
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: otava_test_data.generators.advanced
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: otava_test_data.generators.combiner
   :members:
   :undoc-members:
   :show-inheritance:
```
'''

    api_path = os.path.join(docs_dir, "api.md")
    with open(api_path, "w") as f:
        f.write(api_content)

    # Create benchmark.md
    benchmark_content = '''# Benchmark Guide

## Generating Benchmark Data

Use the CLI to generate a comprehensive benchmark suite:

```bash
otava-gen generate --output-dir ./benchmark --lengths 50 500 --seed 42
```

This creates:
- CSV files for each test case
- `manifest.json` with metadata about each file
- `summary.json` with overall statistics

## Running Otava

```bash
# Example Otava invocation (adjust based on Otava's actual CLI)
otava analyze --input ./benchmark/0001_step_function_L500.csv
```

## Comparing Algorithms

The manifest.json file contains ground truth for each test case:

```python
import json

with open("benchmark/manifest.json") as f:
    manifest = json.load(f)

for entry in manifest:
    print(f"{entry['filename']}: {entry['n_change_points']} change points")
    print(f"  Expected indices: {entry['change_point_indices']}")
```

## Metrics

When comparing algorithms, consider:

1. **True Positive Rate**: % of actual change points detected
2. **False Positive Rate**: % of non-change-points flagged
3. **Location Accuracy**: How close detected points are to actual
4. **Latency**: How many points after change before detection
'''

    bench_path = os.path.join(docs_dir, "benchmark.md")
    with open(bench_path, "w") as f:
        f.write(benchmark_content)

    # Create _static and _templates directories
    os.makedirs(os.path.join(docs_dir, "_static"), exist_ok=True)
    os.makedirs(os.path.join(docs_dir, "_templates"), exist_ok=True)

    print(f"Documentation initialized in {docs_dir}")


@task
def clean(c: Context):
    """Clean build artifacts."""
    patterns = [
        "build/",
        "dist/",
        "*.egg-info/",
        "**/__pycache__/",
        ".pytest_cache/",
        ".ruff_cache/",
        "docs/_build/",
        ".coverage",
        "htmlcov/",
    ]

    for pattern in patterns:
        c.run(f"rm -rf {pattern}", warn=True)

    print("Cleaned build artifacts")


@task
def check(c: Context):
    """Run all checks (lint, format check, tests)."""
    print("Running lint...")
    c.run("uv run ruff check src/", warn=True, pty=True)

    print("\nRunning format check...")
    c.run("uv run ruff format src/ --check", warn=True, pty=True)

    print("\nRunning tests...")
    c.run("uv run pytest src/otava_test_data/tests/test_generators.py -v", pty=True)


@task(pre=[check])
def release(c: Context, version: str = ""):
    """Prepare a release (run checks, update version, build)."""
    if not version:
        print("Error: Please specify version with --version")
        return

    # Update version in pyproject.toml
    c.run(f"sed -i '' 's/version = \".*\"/version = \"{version}\"/' pyproject.toml")

    # Update version in __init__.py
    c.run(
        f"sed -i '' 's/__version__ = \".*\"/__version__ = \"{version}\"/' "
        "src/otava_test_data/__init__.py"
    )

    print(f"Updated version to {version}")
    print("Remember to: git add, commit, tag, and push")


@task
def web(c: Context, host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Run the web visualization server (foreground)."""
    reload_flag = "--reload" if reload else ""
    c.run(
        f"uv run uvicorn otava_test_data.web.main:app "
        f"--host {host} --port {port} {reload_flag}",
        pty=True,
    )


WEB_PID_FILE = "/tmp/otava-web.pid"
WEB_DEFAULT_PORT = 8100


@task
def web_start(c: Context, host: str = "127.0.0.1", port: int = WEB_DEFAULT_PORT, reload: bool = True):
    """Start the web server in the background."""
    import subprocess
    import time
    import urllib.request

    # Check if already running
    if os.path.exists(WEB_PID_FILE):
        with open(WEB_PID_FILE, "r") as f:
            pid = f.read().strip()
        # Check if process is still running
        result = c.run(f"ps -p {pid}", warn=True, hide=True)
        if result.ok:
            print(f"Web server already running (PID: {pid})")
            return
        else:
            # Stale PID file
            os.remove(WEB_PID_FILE)

    cmd = [
        "uv", "run", "uvicorn", "otava_test_data.web.main:app",
        "--host", host, "--port", str(port),
    ]
    if reload:
        cmd.append("--reload")

    # Start in background
    proc = subprocess.Popen(
        cmd,
        # stdout=subprocess.DEVNULL,
        # stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Save PID
    with open(WEB_PID_FILE, "w") as f:
        f.write(str(proc.pid))

    # Wait and check if server started
    time.sleep(2)
    try:
        urllib.request.urlopen(f"http://{host}:{port}/api/generators", timeout=5)
        print(f"Web server started at http://{host}:{port} (PID: {proc.pid})")
    except Exception as e:
        print(f"Warning: Server may not be ready yet - {e}")
        print(f"Check http://{host}:{port} manually")


@task
def web_stop(c: Context):
    """Stop the web server running in the background."""
    if not os.path.exists(WEB_PID_FILE):
        print("Web server is not running (no PID file found)")
        return

    with open(WEB_PID_FILE, "r") as f:
        pid = f.read().strip()

    # Kill the process group (handles child processes from --reload)
    result = c.run(f"pkill -P {pid}", warn=True, hide=True)
    result = c.run(f"kill {pid}", warn=True, hide=True)

    if result.ok:
        print(f"Web server stopped (PID: {pid})")
    else:
        print(f"Process {pid} may already be stopped")

    os.remove(WEB_PID_FILE)


@task
def web_restart(c: Context, host: str = "127.0.0.1", port: int = WEB_DEFAULT_PORT, reload: bool = True):
    """Restart the web server."""
    web_stop(c)
    import time
    time.sleep(1)
    web_start(c, host=host, port=port, reload=reload)


@task
def web_status(c: Context):
    """Check if the web server is running."""
    if not os.path.exists(WEB_PID_FILE):
        print("Web server is not running (no PID file)")
        return

    with open(WEB_PID_FILE, "r") as f:
        pid = f.read().strip()

    result = c.run(f"ps -p {pid} -o pid,command", warn=True, hide=True)
    if result.ok:
        print(f"Web server is running:")
        print(result.stdout)
    else:
        print(f"Web server is not running (stale PID: {pid})")
        os.remove(WEB_PID_FILE)


@task
def web_check(c: Context):
    """Check if the web server starts correctly."""
    import subprocess
    import time
    import urllib.request

    # Start server in background
    proc = subprocess.Popen(
        ["uv", "run", "uvicorn", "otava_test_data.web.main:app",
         "--host", "127.0.0.1", "--port", "8765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        time.sleep(3)  # Wait for server to start

        # Check if server responds
        response = urllib.request.urlopen("http://127.0.0.1:8765/api/generators")
        data = response.read()
        print("Web server check: OK")
        print(f"Generators endpoint returned {len(data)} bytes")

    except Exception as e:
        print(f"Web server check: FAILED - {e}")

    finally:
        proc.terminate()
        proc.wait()
