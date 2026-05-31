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

# Benchmark Guide

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
