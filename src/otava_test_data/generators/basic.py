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
Basic building block time series generators.

These generators create fundamental time series patterns used in performance
testing scenarios. Each generator returns a TimeSeries object containing
the data and metadata about any change points present.
"""

from dataclasses import dataclass, field
import numpy as np
from numpy.typing import NDArray


@dataclass
class ChangePoint:
    """Represents a change point in a time series."""

    index: int
    """Index where the change occurs."""

    change_type: str
    """Type of change: 'step', 'outlier', 'variance', 'regression_start', 'regression_end'."""

    before_value: float | None = None
    """Mean/value before the change point."""

    after_value: float | None = None
    """Mean/value after the change point."""

    description: str = ""
    """Human-readable description of this change point."""


@dataclass
class TimeSeries:
    """
    Container for time series data with change point metadata.

    Attributes:
        data: The time series values as a numpy array.
        change_points: List of known change points in the series.
        generator_name: Name of the generator that created this series.
        parameters: Dictionary of parameters used to generate the series.
    """

    data: NDArray[np.float64]
    change_points: list[ChangePoint] = field(default_factory=list)
    generator_name: str = ""
    parameters: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> float:
        return self.data[idx]

    @property
    def length(self) -> int:
        """Return the length of the time series."""
        return len(self.data)

    def to_csv(self, filename: str, include_metadata: bool = True) -> None:
        """Export time series to CSV file."""
        import pandas as pd

        df = pd.DataFrame({
            "index": range(len(self.data)),
            "value": self.data,
        })

        if include_metadata:
            # Add change point markers
            df["is_change_point"] = False
            for cp in self.change_points:
                if 0 <= cp.index < len(self.data):
                    df.loc[cp.index, "is_change_point"] = True

        df.to_csv(filename, index=False)

    def get_change_point_indices(self) -> list[int]:
        """Return list of change point indices."""
        return [cp.index for cp in self.change_points]


def constant(length: int, value: float = 100.0, seed: int | None = None) -> TimeSeries:
    """
    Generate a constant time series: S = x, x, x, x...

    This represents an ideal performance test with no variation.

    Args:
        length: Number of data points (typically 50 or 500).
        value: The constant value.
        seed: Random seed (unused, for API consistency).

    Returns:
        TimeSeries with constant values and no change points.

    Example:
        >>> ts = constant(length=100, value=50.0)
        >>> all(v == 50.0 for v in ts.data)
        True
    """
    data = np.full(length, value, dtype=np.float64)
    return TimeSeries(
        data=data,
        change_points=[],
        generator_name="constant",
        parameters={"length": length, "value": value},
    )


def noise_normal(
    length: int,
    mean: float = 100.0,
    sigma: float = 5.0,
    seed: int | None = None,
    bounded: bool = True,
) -> TimeSeries:
    """
    Generate normally distributed noise: S = x1, x2, x3... where X ~ N(mean, sigma).

    This represents typical performance test output with random variation.
    When bounded=True, values are clipped to within 4 standard deviations
    (99.99% percentile), making it possible for algorithms to correctly
    detect 100% of cases.

    Args:
        length: Number of data points.
        mean: Mean of the distribution.
        sigma: Standard deviation.
        seed: Random seed for reproducibility.
        bounded: If True, clip values to mean +/- 4*sigma.

    Returns:
        TimeSeries with normally distributed values and no change points.
    """
    rng = np.random.default_rng(seed)
    data = rng.normal(mean, sigma, length)

    if bounded:
        lower = mean - 4 * sigma
        upper = mean + 4 * sigma
        data = np.clip(data, lower, upper)

    return TimeSeries(
        data=data,
        change_points=[],
        generator_name="noise_normal",
        parameters={
            "length": length,
            "mean": mean,
            "sigma": sigma,
            "seed": seed,
            "bounded": bounded,
        },
    )


def noise_uniform(
    length: int,
    min_val: float = 90.0,
    max_val: float = 110.0,
    seed: int | None = None,
) -> TimeSeries:
    """
    Generate uniformly distributed noise (white noise): S = random(min, max).

    Also known as static noise. All values are equally likely within the range.

    Args:
        length: Number of data points.
        min_val: Minimum value.
        max_val: Maximum value.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with uniformly distributed values and no change points.
    """
    rng = np.random.default_rng(seed)
    data = rng.uniform(min_val, max_val, length)

    return TimeSeries(
        data=data,
        change_points=[],
        generator_name="noise_uniform",
        parameters={
            "length": length,
            "min_val": min_val,
            "max_val": max_val,
            "seed": seed,
        },
    )


def outlier(
    length: int,
    baseline: float = 100.0,
    outlier_value: float = 150.0,
    outlier_index: int | None = None,
    sigma: float = 0.0,
    seed: int | None = None,
) -> TimeSeries:
    """
    Generate a time series with a single outlier (anomaly).

    S = x, x, x, x, x, x', x, x... where x' != x

    An outlier is a single deviating point, which may be indistinguishable
    from a very short regression (single point).

    Args:
        length: Number of data points.
        baseline: The normal/baseline value.
        outlier_value: The outlier value.
        outlier_index: Position of the outlier. If None, placed at length//2.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with one outlier marked as a change point.
    """
    rng = np.random.default_rng(seed)

    if outlier_index is None:
        outlier_index = length // 2

    if outlier_index < 0 or outlier_index >= length:
        raise ValueError(f"outlier_index must be in [0, {length}), got {outlier_index}")

    data = np.full(length, baseline, dtype=np.float64)

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    data[outlier_index] = outlier_value

    change_points = [
        ChangePoint(
            index=outlier_index,
            change_type="outlier",
            before_value=baseline,
            after_value=outlier_value,
            description=f"Single outlier at index {outlier_index}",
        )
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="outlier",
        parameters={
            "length": length,
            "baseline": baseline,
            "outlier_value": outlier_value,
            "outlier_index": outlier_index,
            "sigma": sigma,
            "seed": seed,
        },
    )


def step_function(
    length: int,
    value_before: float = 100.0,
    value_after: float = 120.0,
    change_index: int | None = None,
    sigma: float = 0.0,
    seed: int | None = None,
) -> TimeSeries:
    """
    Generate a step function (single change point).

    S = x1, x1, x1, x2, x2, x2, x2...

    This represents a performance regression or improvement that persists.

    Args:
        length: Number of data points.
        value_before: Value before the change point.
        value_after: Value after the change point.
        change_index: Position of the change. If None, placed at length//2.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with one step change point.
    """
    rng = np.random.default_rng(seed)

    if change_index is None:
        change_index = length // 2

    if change_index < 1 or change_index >= length:
        raise ValueError(f"change_index must be in [1, {length}), got {change_index}")

    data = np.empty(length, dtype=np.float64)
    data[:change_index] = value_before
    data[change_index:] = value_after

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    change_points = [
        ChangePoint(
            index=change_index,
            change_type="step",
            before_value=value_before,
            after_value=value_after,
            description=f"Step change from {value_before} to {value_after}",
        )
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="step_function",
        parameters={
            "length": length,
            "value_before": value_before,
            "value_after": value_after,
            "change_index": change_index,
            "sigma": sigma,
            "seed": seed,
        },
    )


def regression_fix(
    length: int,
    value_normal: float = 100.0,
    value_regression: float = 130.0,
    value_fixed: float | None = None,
    regression_start: int | None = None,
    regression_duration: int = 10,
    sigma: float = 0.0,
    seed: int | None = None,
) -> TimeSeries:
    """
    Generate a regression followed by a fix.

    S = x1, x1... x2, ...x2, x3, x3, x3...

    The amount of x2 points is small compared to x1 and x3, but at least 2 points.
    Special case: x1 == x3 (fixed back to original value).
    Special case: x2 is a single point (indistinguishable from outlier).

    Args:
        length: Number of data points.
        value_normal: Normal/baseline value (x1).
        value_regression: Value during regression (x2).
        value_fixed: Value after fix (x3). If None, defaults to value_normal.
        regression_start: Index where regression begins. If None, placed at length//3.
        regression_duration: How many points in the regression state (minimum 2).
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with regression and fix change points.
    """
    rng = np.random.default_rng(seed)

    if value_fixed is None:
        value_fixed = value_normal

    if regression_duration < 2:
        raise ValueError("regression_duration must be at least 2")

    if regression_start is None:
        regression_start = length // 3

    regression_end = regression_start + regression_duration

    if regression_start < 1:
        raise ValueError(f"regression_start must be >= 1, got {regression_start}")
    if regression_end >= length:
        raise ValueError(
            f"regression_start + regression_duration must be < {length}, "
            f"got {regression_end}"
        )

    data = np.empty(length, dtype=np.float64)
    data[:regression_start] = value_normal
    data[regression_start:regression_end] = value_regression
    data[regression_end:] = value_fixed

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    change_points = [
        ChangePoint(
            index=regression_start,
            change_type="regression_start",
            before_value=value_normal,
            after_value=value_regression,
            description=f"Regression starts: {value_normal} -> {value_regression}",
        ),
        ChangePoint(
            index=regression_end,
            change_type="regression_end",
            before_value=value_regression,
            after_value=value_fixed,
            description=f"Regression fixed: {value_regression} -> {value_fixed}",
        ),
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="regression_fix",
        parameters={
            "length": length,
            "value_normal": value_normal,
            "value_regression": value_regression,
            "value_fixed": value_fixed,
            "regression_start": regression_start,
            "regression_duration": regression_duration,
            "sigma": sigma,
            "seed": seed,
        },
    )
