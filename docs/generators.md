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

# Time Series Generators

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
