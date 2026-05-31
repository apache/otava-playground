<!--
  Licensed to the Apache Software Foundation (ASF) under one or more
  contributor license agreements.  See the NOTICE file distributed with
  this work for additional information regarding copyright ownership.
  The ASF licenses this file to You under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with
  the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Otava Test Data

Test data generators and Visualization for [Apache Otava](https://github.com/apache/otava) change point detection.

## Web Visualizer

The package includes an interactive web visualizer for exploring test patterns and comparing change point detection results against ground truth.

![Step Function Detection](https://raw.githubusercontent.com/jdrumgoole/otava-test-data/main/docs/_static/screenshots/step-function-sigma-2.png)

**Features:**
- Generate and visualize 17 different test patterns
- Compare three analysis methods: Otava (statistical), Moving Average, and Boundary detection
- View accuracy metrics (precision, recall, F1 score)
- Adjust parameters in real-time and see results instantly

### Multiple Change Points

Detect multiple successive changes in your data:

![Multiple Changes Detection](https://raw.githubusercontent.com/jdrumgoole/otava-test-data/main/docs/_static/screenshots/multiple-changes.png)

### Variance Changes

Detect changes in data volatility even when the mean stays constant:

![Variance Change Detection](https://raw.githubusercontent.com/jdrumgoole/otava-test-data/main/docs/_static/screenshots/variance-change.png)

### Starting the Visualizer

```bash
pip install otava-test-data[web]

# Start the web server
otava-web
# Or with invoke tasks
inv web-start
```

Then open http://127.0.0.1:8100 in your browser.

## Installation

```bash
pip install otava-test-data
```

Or with all optional dependencies:

```bash
pip install otava-test-data[all]
```

## Quick Start

```python
from otava_test_data import step_function, noise_normal, combine

# Generate a step function (single change point) with realistic noise
step = step_function(length=500, value_before=100, value_after=120)
noise = noise_normal(length=500, mean=0, sigma=5)
combined = combine(step, noise)

# Export to CSV for Otava analysis
combined.to_csv("test_data.csv")

# Access ground truth change point information
for cp in combined.change_points:
    print(f"Change at index {cp.index}: {cp.description}")
```

## Available Generators

### Basic Building Blocks

| Generator | Description |
|-----------|-------------|
| `constant` | Constant value: `S = x, x, x, x...` |
| `noise_normal` | Normal distribution: `S ~ N(mean, sigma)` |
| `noise_uniform` | Uniform distribution: `S ~ U(min, max)` |
| `outlier` | Single anomaly: `S = x, x, x', x, x...` |
| `step_function` | Single change point: `S = x1, x1, x2, x2...` |
| `regression_fix` | Temporary regression: `S = x1, x2, x1...` |

### Advanced Patterns

| Generator | Description |
|-----------|-------------|
| `banding` | Oscillation between two values |
| `variance_change` | Constant mean, changing variance |
| `phase_change` | Phase shift in periodic signal |
| `multiple_changes` | Multiple consecutive step changes |

## CLI Tool

```bash
# Generate test suite
otava-gen generate --output-dir ./test_data --lengths 50 500 --seed 42

# List available generators
otava-gen list

# Get info about a generator
otava-gen info step_function
```

## Documentation

Full documentation available at [Read the Docs](https://otava-test-data.readthedocs.io/).

## License

Apache License 2.0
