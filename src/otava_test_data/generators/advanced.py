"""
Advanced time series generators for more complex phenomena.

These generators create patterns that represent more nuanced behaviors
seen in real performance testing scenarios.
"""

import numpy as np
from numpy.typing import NDArray

from otava_test_data.generators.basic import TimeSeries, ChangePoint


def banding(
    length: int,
    value1: float = 100.0,
    value2: float = 105.0,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a banding time series - oscillating randomly between two values.

    S = x1, x2, x2, x1, x2, x1, x1, x1, x2, x2, x1, x2, x2...

    Banding is a form of noise (unwanted change) where results oscillate
    randomly between two values. Typically:
    - abs(x2 - x1) << x1 (the band gap is small relative to values)
    - When random noise is mixed in: x1, x2 > std dev

    Args:
        length: Number of data points.
        value1: First band value.
        value2: Second band value.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with banding pattern (no explicit change points).
    """
    rng = np.random.default_rng(seed)

    # Randomly choose between the two values for each point
    choices = rng.choice([value1, value2], size=length)
    data = choices.astype(np.float64)

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    # Banding doesn't have explicit change points - it's a noise pattern
    return TimeSeries(
        data=data,
        change_points=[],
        generator_name="banding",
        parameters={
            "length": length,
            "value1": value1,
            "value2": value2,
            "sigma": sigma,
            "seed": seed,
        },
    )


def variance_change(
    length: int,
    mean: float = 100.0,
    sigma_before: float = 2.0,
    sigma_after: float = 10.0,
    change_index: int | None = None,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with constant mean but changing variance.

    S = N(mean, sigma1)..., N(mean, sigma2)...

    The mean stays the same, but the spread of values changes at a point.
    This can indicate a change in test stability or environmental factors.

    Args:
        length: Number of data points.
        mean: Mean value (constant throughout).
        sigma_before: Standard deviation before change point.
        sigma_after: Standard deviation after change point.
        change_index: Position of the variance change. If None, placed at length//2.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with one variance change point.
    """
    rng = np.random.default_rng(seed)

    if change_index is None:
        change_index = length // 2

    if change_index < 1 or change_index >= length:
        raise ValueError(f"change_index must be in [1, {length}), got {change_index}")

    data = np.empty(length, dtype=np.float64)
    data[:change_index] = rng.normal(mean, sigma_before, change_index)
    data[change_index:] = rng.normal(mean, sigma_after, length - change_index)

    change_points = [
        ChangePoint(
            index=change_index,
            change_type="variance",
            before_value=sigma_before,
            after_value=sigma_after,
            description=f"Variance change from sigma={sigma_before} to sigma={sigma_after}",
        )
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="variance_change",
        parameters={
            "length": length,
            "mean": mean,
            "sigma_before": sigma_before,
            "sigma_after": sigma_after,
            "change_index": change_index,
            "seed": seed,
        },
    )


def phase_change(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 20,
    change_index: int | None = None,
    phase_shift: float = np.pi / 2,  # Default: cos -> sin (90 degree shift)
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with constant mean and variance but phase changes.

    S = cos(x)..., sin(x)...

    The underlying periodic pattern shifts phase at a point. While periodic
    patterns are not typical in performance testing (mentioned in spec as
    things we do NOT encounter), this is included for completeness in testing
    detection algorithms.

    Args:
        length: Number of data points.
        amplitude: Amplitude of the oscillation.
        baseline: Baseline value around which oscillation occurs.
        period: Number of points per cycle.
        change_index: Position of the phase change. If None, placed at length//2.
        phase_shift: Amount of phase shift in radians (default pi/2 = cos to sin).
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with one phase change point.
    """
    rng = np.random.default_rng(seed)

    if change_index is None:
        change_index = length // 2

    if change_index < 1 or change_index >= length:
        raise ValueError(f"change_index must be in [1, {length}), got {change_index}")

    # Generate x values for the cosine/sine
    x = np.arange(length) * 2 * np.pi / period

    data = np.empty(length, dtype=np.float64)
    # Before change: cos(x)
    data[:change_index] = baseline + amplitude * np.cos(x[:change_index])
    # After change: cos(x + phase_shift) = sin(x) when phase_shift = pi/2
    data[change_index:] = baseline + amplitude * np.cos(x[change_index:] + phase_shift)

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    change_points = [
        ChangePoint(
            index=change_index,
            change_type="phase",
            before_value=0.0,
            after_value=phase_shift,
            description=f"Phase shift of {phase_shift:.3f} radians",
        )
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="phase_change",
        parameters={
            "length": length,
            "amplitude": amplitude,
            "baseline": baseline,
            "period": period,
            "change_index": change_index,
            "phase_shift": phase_shift,
            "sigma": sigma,
            "seed": seed,
        },
    )

def amplitude_change_clean(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 20,
    amplitude_change: float = 1.5,
    change_index: int | None = None,
    seed: int | None = 42,
    sigma: float | None = None
) -> TimeSeries:
    change_indexes = None if change_index is None else [change_index]
    amplitude_changes = None if amplitude_change is None else [amplitude_change]
    return multiple_amplitude_changes_clean(length, amplitude, baseline, period, amplitude_changes, change_indexes)

def multiple_amplitude_changes_clean(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 100,
    amplitude_changes: list[float] = [1.5, 1.3, 1.4],
    change_indexes: list[int] | None = None,
    seed: int | None = 42,
    sigma: float | None = None
) -> TimeSeries:
    """
    Generate a time series with constant mean, but a change in amplitude (aka variance).

    S = cos(x)..., 1.5 * cos(x)...

    Args:
        length: Number of data points.
        amplitude: Amplitude of the oscillation.
        baseline: Baseline value around which oscillation occurs.
        period: Number of points per cycle.
        amplitude_changes: Multiply amplitude beginning at change_index(es). If change_indexes is also given, must be same length
        change_indexes: List of positions of the amplitude change(s). If None, randomly generate len(amplitude_changes) indexes

    Returns:
        TimeSeries with N change points where the mean remains constant but amplitude (and hence variance) change.
    """
    _ = seed
    _ = sigma
    rng = np.full(length, baseline)

    if change_indexes is None:
        change_indexes = np.random.randint(low=0, high=length, size=len(amplitude_changes))
        change_indexes.sort()

    data = np.empty(length, dtype=np.float64)
    change_points = []
    prev_index = 0
    print(data, change_indexes, amplitude_changes, length)
    for change_index, amplitude_change in zip(np.append(change_indexes, length), [1.0] + amplitude_changes):

        if change_index < 1 or change_index > length:
                raise ValueError(f"change_index must be in [1, {length}], got {change_index}")

        # Generate x values for the cosine
        x = np.arange(prev_index, change_index) * 2 * np.pi / period
        print(prev_index, change_index)
        data[prev_index:change_index] = baseline + amplitude_change * amplitude * np.cos(x  )

        change_points.append(
            ChangePoint(
                index=change_index,
                change_type="amplitude",
                before_value=amplitude,
                after_value=amplitude*amplitude_change,
                description=f"Amplitude change {amplitude_change:.3f}x",
            )
        )
        prev_index = change_index


    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="amplitude_change",
        parameters={
            "length": length,
            "amplitude": amplitude,
            "baseline": baseline,
            "period": period,
            "change_index": change_index,
            "amplitude_change": amplitude_change,
            "sigma": sigma,
            "seed": seed,
        },
    )


def multiple_changes(
    length: int,
    values: list[float] | None = None,
    change_indices: list[int] | None = None,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple consecutive changes.

    S = x0, x0, x0... x1, x2, ... xn, xn, xn...

    Where x0 < x1 < x2 ... < xn (monotonically increasing) or any other
    sequence of distinct values.

    This represents multiple independent improvements or regressions merged
    back to back in performance testing.

    Args:
        length: Number of data points.
        values: List of values for each segment. If None, defaults to
                [100, 110, 120, 130] (three changes).
        change_indices: List of indices where changes occur. Must have
                       len(values) - 1 elements. If None, evenly distributed.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple step change points.

    Example:
        >>> ts = multiple_changes(100, values=[100, 120, 140], change_indices=[30, 60])
        >>> len(ts.change_points)
        2
    """
    rng = np.random.default_rng(seed)

    if values is None:
        values = [100.0, 110.0, 120.0, 130.0]

    n_segments = len(values)
    n_changes = n_segments - 1

    if n_changes < 1:
        raise ValueError("values must have at least 2 elements")

    if change_indices is None:
        # Evenly distribute change points
        segment_length = length // n_segments
        change_indices = [segment_length * (i + 1) for i in range(n_changes)]

    if len(change_indices) != n_changes:
        raise ValueError(
            f"change_indices must have {n_changes} elements, got {len(change_indices)}"
        )

    # Validate change indices are in order and within bounds
    all_indices = [0] + list(change_indices) + [length]
    for i in range(len(all_indices) - 1):
        if all_indices[i] >= all_indices[i + 1]:
            raise ValueError("change_indices must be strictly increasing")

    data = np.empty(length, dtype=np.float64)

    # Fill each segment
    segment_starts = [0] + list(change_indices)
    segment_ends = list(change_indices) + [length]

    for i, (start, end, value) in enumerate(zip(segment_starts, segment_ends, values)):
        data[start:end] = value

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    # Create change points
    change_points = []
    for i, idx in enumerate(change_indices):
        change_points.append(
            ChangePoint(
                index=idx,
                change_type="step",
                before_value=values[i],
                after_value=values[i + 1],
                description=f"Change {i + 1}: {values[i]} -> {values[i + 1]}",
            )
        )

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="multiple_changes",
        parameters={
            "length": length,
            "values": values,
            "change_indices": change_indices,
            "sigma": sigma,
            "seed": seed,
        },
    )

def outlier_clean(
    length: int,
    baseline: float = 100.0,
    outlier_value: float = 150.0,
    outlier_index: int | None = None,
    seed: int | None = 42,
) -> TimeSeries:
    idx = None if outlier_index is None else [int]
    return multiple_outliers_clean(length, baseline, outlier_value, idx, 1, 0, seed)

def multiple_outliers_clean(
    length: int,
    baseline: float = 100.0,
    outlier_value: float = 150.0,
    outlier_indices: list[int] | None = None,
    n_outliers: int = 3,
    sigma: int | None = 0,
    seed: int | None = 42,
) -> TimeSeries:
    t = multiple_outliers(length, baseline, outlier_value, outlier_indices, n_outliers, 0, seed)
    return t

def multiple_outliers(
    length: int,
    baseline: float = 100.0,
    outlier_value: float = 150.0,
    outlier_indices: list[int] | None = None,
    n_outliers: int = 3,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple outliers.

    Extension of the single outlier case - multiple isolated anomalous points.

    Args:
        length: Number of data points.
        baseline: The normal/baseline value.
        outlier_value: The outlier value(s).
        outlier_indices: Specific indices for outliers. If None, randomly placed.
        n_outliers: Number of outliers if outlier_indices is None.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple outlier change points.
    """
    rng = np.random.default_rng(seed)

    if outlier_indices is None:
        # Randomly place outliers, ensuring they're not adjacent
        available = list(range(1, length - 1))  # Avoid first and last
        if n_outliers > len(available):
            raise ValueError(f"Cannot place {n_outliers} outliers in length {length}")

        outlier_indices = sorted(rng.choice(available, size=n_outliers, replace=False))

    data = np.full(length, baseline, dtype=np.float64)

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    for idx in outlier_indices:
        data[idx] = outlier_value

    change_points = [
        ChangePoint(
            index=idx,
            change_type="outlier",
            before_value=baseline,
            after_value=outlier_value,
            description=f"Outlier at index {idx}",
        )
        for idx in outlier_indices
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="multiple_outliers",
        parameters={
            "length": length,
            "baseline": baseline,
            "outlier_value": outlier_value,
            "outlier_indices": list(outlier_indices),
            "sigma": sigma,
            "seed": seed,
        },
    )



def multiple_variance_changes(
    length: int,
    mean: float = 100.0,
    sigmas: list[float] | None = None,
    change_indices: list[int] | None = None,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple variance changes.

    Extension of variance_change - variance changes multiple times while
    mean stays constant.

    Args:
        length: Number of data points.
        mean: Constant mean value.
        sigmas: List of sigma values for each segment.
        change_indices: Indices where variance changes occur.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple variance change points.
    """
    rng = np.random.default_rng(seed)

    if sigmas is None:
        sigmas = [2.0, 8.0, 3.0, 10.0]

    n_segments = len(sigmas)
    n_changes = n_segments - 1

    if change_indices is None:
        segment_length = length // n_segments
        change_indices = [segment_length * (i + 1) for i in range(n_changes)]

    if len(change_indices) != n_changes:
        raise ValueError(
            f"change_indices must have {n_changes} elements, got {len(change_indices)}"
        )

    data = np.empty(length, dtype=np.float64)

    segment_starts = [0] + list(change_indices)
    segment_ends = list(change_indices) + [length]

    for start, end, sigma in zip(segment_starts, segment_ends, sigmas):
        segment_length = end - start
        data[start:end] = rng.normal(mean, sigma, segment_length)

    change_points = [
        ChangePoint(
            index=idx,
            change_type="variance",
            before_value=sigmas[i],
            after_value=sigmas[i + 1],
            description=f"Variance change: sigma {sigmas[i]} -> {sigmas[i + 1]}",
        )
        for i, idx in enumerate(change_indices)
    ]

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="multiple_variance_changes",
        parameters={
            "length": length,
            "mean": mean,
            "sigmas": sigmas,
            "change_indices": change_indices,
            "seed": seed,
        },
    )

def multiple_regression_fix_clean(
    length: int,
    value_normal: float = 100.0,
    value_regression: float = 130.0,
    n_regressions: int = 3,
    regression_duration: int | None = None,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    return multiple_regression_fix(length, value_normal, value_regression,n_regressions,regression_duration, 0.0, seed)

def multiple_regression_fix(
    length: int,
    value_normal: float = 100.0,
    value_regression: float = 130.0,
    n_regressions: int = 3,
    regression_duration: int | None = None,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple regression+fix cycles.

    Multiple temporary regressions that each get fixed, returning to normal.

    Args:
        length: Number of data points.
        value_normal: The normal/baseline value.
        value_regression: The regression value.
        n_regressions: Number of regression cycles.
        regression_duration: Duration of each regression. If None, auto-calculated.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple regression+fix change points.
    """
    rng = np.random.default_rng(seed)

    # Calculate segment sizes
    n_segments = n_regressions * 2 + 1  # normal, reg, normal, reg, normal, ...
    segment_length = length // n_segments
    if regression_duration is None:
        regression_duration = segment_length

    data = np.full(length, value_normal, dtype=np.float64)
    change_points = []

    for i in range(n_regressions):
        # Start of regression
        reg_start = segment_length * (2 * i + 1)
        reg_end = min(reg_start + regression_duration, length)
        if reg_start < length:
            data[reg_start:reg_end] = value_regression
            change_points.append(
                ChangePoint(
                    index=reg_start,
                    change_type="regression",
                    before_value=value_normal,
                    after_value=value_regression,
                    description=f"Regression {i+1} start",
                )
            )
            if reg_end < length:
                change_points.append(
                    ChangePoint(
                        index=reg_end,
                        change_type="fix",
                        before_value=value_regression,
                        after_value=value_normal,
                        description=f"Regression {i+1} fix",
                    )
                )

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="multiple_regression_fix",
        parameters={
            "length": length,
            "value_normal": value_normal,
            "value_regression": value_regression,
            "n_regressions": n_regressions,
            "regression_duration": regression_duration,
            "sigma": sigma,
            "seed": seed,
        },
    )


def multiple_banding(
    length: int,
    values: list[float] | str | None = [80,103,130],
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple banding segments.

    Each segment oscillates between a different pair of values.

    Args:
        length: Number of data points.
        value_pairs: list() of floats. The graph consists of these constants + sigma. A comma separated string is acceptable.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple banding segments.
    """
    rng = np.random.default_rng(seed)

    if values is None:
        values = [95.0, 105.0, 100.0]
    if isinstance(values, str):
        values = values.split(",")
        values =[float(s) for s in values]

    data = np.random.randint(size=length, low=0, high=3)
    change_points = []

    for i in range(length):
        data[i] = values[data[i]]

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    return TimeSeries(
        data=data,
        change_points=[],
        generator_name="multiple_banding",
        parameters={
            "length": length,
            "values": values,
            "sigma": sigma,
            "seed": seed,
        },
    )


def multiple_phase_changes_clean(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 20,
    n_changes: int = 3,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    return multiple_phase_changes(length, amplitude, baseline, period, n_changes, 0.0, 42)

def multiple_phase_changes(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 20,
    n_changes: int = 3,
    sigma: float = 0.0,
    seed: int | None = 42,
) -> TimeSeries:
    """
    Generate a time series with multiple phase changes.

    A periodic signal that undergoes multiple phase shifts.

    Args:
        length: Number of data points.
        amplitude: Amplitude of the periodic signal.
        baseline: Baseline/center value.
        period: Period of the oscillation.
        n_changes: Number of phase changes.
        sigma: If > 0, add normal noise with this standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        TimeSeries with multiple phase change points.
    """
    rng = np.random.default_rng(seed)

    segment_length = length // (n_changes + 1)
    data = np.empty(length, dtype=np.float64)
    change_points = []

    phase_shifts = [0] + [np.pi / 2 * (i + 1) for i in range(n_changes)]

    for i, phase in enumerate(phase_shifts):
        start = i * segment_length
        end = (i + 1) * segment_length if i < n_changes else length

        x = np.arange(start, end)
        data[start:end] = baseline + amplitude * np.cos(2 * np.pi * x / period + phase)

        if i > 0:
            change_points.append(
                ChangePoint(
                    index=start,
                    change_type="phase",
                    before_value=phase_shifts[i-1],
                    after_value=phase,
                    description=f"Phase shift to {phase:.2f} rad",
                )
            )

    if sigma > 0:
        data += rng.normal(0, sigma, length)

    return TimeSeries(
        data=data,
        change_points=change_points,
        generator_name="multiple_phase_changes",
        parameters={
            "length": length,
            "amplitude": amplitude,
            "baseline": baseline,
            "period": period,
            "n_changes": n_changes,
            "sigma": sigma,
            "seed": seed,
        },
    )


# =============================================================================
# Uniform Noise Variants
# =============================================================================

def outlier_uniform(
    length: int,
    baseline: float = 100.0,
    outlier_value: float = 150.0,
    outlier_index: int | None = None,
    noise_range: float = 10.0,
    seed: int | None = 42,
) -> TimeSeries:
    """Single outlier with uniform noise."""
    rng = np.random.default_rng(seed)

    if outlier_index is None:
        outlier_index = length // 2

    data = np.full(length, baseline, dtype=np.float64)
    data[outlier_index] = outlier_value

    # Add uniform noise
    data += rng.uniform(-noise_range/2, noise_range/2, length)

    return TimeSeries(
        data=data,
        change_points=[
            ChangePoint(
                index=outlier_index,
                change_type="outlier",
                before_value=baseline,
                after_value=outlier_value,
                description=f"Single outlier at index {outlier_index}",
            )
        ],
        generator_name="outlier_uniform",
        parameters={"length": length, "baseline": baseline, "outlier_value": outlier_value,
                    "outlier_index": outlier_index, "noise_range": noise_range, "seed": seed},
    )


def step_function_uniform(
    length: int,
    value_before: float = 100.0,
    value_after: float = 120.0,
    change_index: int | None = None,
    noise_range: float = 10.0,
    seed: int | None = 42,
) -> TimeSeries:
    """Step function with uniform noise."""
    rng = np.random.default_rng(seed)

    if change_index is None:
        change_index = length // 2

    data = np.empty(length, dtype=np.float64)
    data[:change_index] = value_before
    data[change_index:] = value_after

    data += rng.uniform(-noise_range/2, noise_range/2, length)

    return TimeSeries(
        data=data,
        change_points=[
            ChangePoint(
                index=change_index,
                change_type="step",
                before_value=value_before,
                after_value=value_after,
                description=f"Step from {value_before} to {value_after}",
            )
        ],
        generator_name="step_function_uniform",
        parameters={"length": length, "value_before": value_before, "value_after": value_after,
                    "change_index": change_index, "noise_range": noise_range, "seed": seed},
    )


def regression_fix_uniform(
    length: int,
    value_normal: float = 100.0,
    value_regression: float = 130.0,
    regression_start: int | None = None,
    regression_duration: int = 20,
    noise_range: float = 10.0,
    seed: int | None = 42,
) -> TimeSeries:
    """Regression + fix pattern with uniform noise."""
    rng = np.random.default_rng(seed)

    if regression_start is None:
        regression_start = length // 3

    regression_end = min(regression_start + regression_duration, length - 1)

    data = np.full(length, value_normal, dtype=np.float64)
    data[regression_start:regression_end] = value_regression

    data += rng.uniform(-noise_range/2, noise_range/2, length)

    change_points = [
        ChangePoint(index=regression_start, change_type="regression",
                    before_value=value_normal, after_value=value_regression,
                    description="Performance regression"),
    ]
    if regression_end < length:
        change_points.append(
            ChangePoint(index=regression_end, change_type="fix",
                        before_value=value_regression, after_value=value_normal,
                        description="Regression fixed")
        )

    return TimeSeries(
        data=data, change_points=change_points, generator_name="regression_fix_uniform",
        parameters={"length": length, "value_normal": value_normal, "value_regression": value_regression,
                    "regression_start": regression_start, "regression_duration": regression_duration,
                    "noise_range": noise_range, "seed": seed},
    )


def banding_uniform(
    length: int,
    value1: float = 100.0,
    value2: float = 105.0,
    noise_range: float = 4.0,
    seed: int | None = 42,
) -> TimeSeries:
    """Banding pattern with uniform noise."""
    rng = np.random.default_rng(seed)

    choices = rng.choice([value1, value2], size=length)
    data = choices.astype(np.float64)
    data += rng.uniform(-noise_range/2, noise_range/2, length)

    return TimeSeries(
        data=data, change_points=[], generator_name="banding_uniform",
        parameters={"length": length, "value1": value1, "value2": value2,
                    "noise_range": noise_range, "seed": seed},
    )


def phase_change_uniform(
    length: int,
    amplitude: float = 10.0,
    baseline: float = 100.0,
    period: int = 20,
    change_index: int | None = None,
    noise_range: float = 4.0,
    seed: int | None = 42,
) -> TimeSeries:
    """Phase change with uniform noise."""
    rng = np.random.default_rng(seed)

    if change_index is None:
        change_index = length // 2

    data = np.empty(length, dtype=np.float64)
    x = np.arange(length) * 2 * np.pi / period

    data[:change_index] = baseline + amplitude * np.cos(x[:change_index])
    data[change_index:] = baseline + amplitude * np.sin(x[change_index:])

    data += rng.uniform(-noise_range/2, noise_range/2, length)

    return TimeSeries(
        data=data,
        change_points=[
            ChangePoint(index=change_index, change_type="phase",
                        before_value=0.0, after_value=np.pi/2,
                        description="Phase shift: cos -> sin")
        ],
        generator_name="phase_change_uniform",
        parameters={"length": length, "amplitude": amplitude, "baseline": baseline,
                    "period": period, "change_index": change_index,
                    "noise_range": noise_range, "seed": seed},
    )
