#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""
Otava Test Data - Test data generators and Visualization for Apache Otava change point detection.

This package provides generators for creating synthetic time series data
with known change points for testing and visualizing change point detection
algorithms.
"""

__version__ = "0.1.9"

from otava_test_data.generators.basic import (
    constant,
    noise_normal,
    noise_uniform,
    outlier,
    step_function,
    regression_fix,
)
from otava_test_data.generators.advanced import (
    banding,
    variance_change,
    phase_change,
    multiple_changes,
)
from otava_test_data.generators.combiner import combine, TimeSeries

__all__ = [
    "constant",
    "noise_normal",
    "noise_uniform",
    "outlier",
    "step_function",
    "regression_fix",
    "banding",
    "variance_change",
    "phase_change",
    "multiple_changes",
    "combine",
    "TimeSeries",
]
