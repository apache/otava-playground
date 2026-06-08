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
Combiner module for composing time series building blocks.

Provides utilities to combine multiple time series patterns and generate
all possible combinations of building blocks.
"""

from typing import Callable
from itertools import product
import numpy as np

from otava_test_data.generators.basic import TimeSeries, ChangePoint


def combine(
    *series_list: TimeSeries,
    operation: str = "add",
) -> TimeSeries:
    """
    Combine multiple time series using the specified operation.

    This allows creating complex patterns by combining basic building blocks.
    For example: step_function + noise_normal creates a step with realistic noise.

    Args:
        *series_list: Variable number of TimeSeries to combine.
        operation: How to combine values:
            - "add": Sum the values (default)
            - "multiply": Multiply the values
            - "concatenate": Join series end-to-end

    Returns:
        Combined TimeSeries with merged change points.

    Example:
        >>> step = step_function(100, value_before=100, value_after=120)
        >>> noise = noise_normal(100, mean=0, sigma=5)
        >>> combined = combine(step, noise, operation="add")
    """
    if len(series_list) < 2:
        raise ValueError("At least two TimeSeries required for combining")

    if operation == "concatenate":
        return _concatenate_series(series_list)

    # For add/multiply, all series must have same length
    lengths = [len(s) for s in series_list]
    if len(set(lengths)) > 1:
        raise ValueError(
            f"All TimeSeries must have same length for '{operation}'. Got: {lengths}"
        )

    length = lengths[0]

    if operation == "add":
        data = np.sum([s.data for s in series_list], axis=0)
    elif operation == "multiply":
        data = np.prod([s.data for s in series_list], axis=0)
    else:
        raise ValueError(f"Unknown operation: {operation}")

    # Merge all change points
    all_change_points = []
    for s in series_list:
        all_change_points.extend(s.change_points)

    # Sort by index
    all_change_points.sort(key=lambda cp: cp.index)

    # Build combined generator name and parameters
    generator_names = [s.generator_name for s in series_list]
    combined_name = f"combine({', '.join(generator_names)})"

    return TimeSeries(
        data=data,
        change_points=all_change_points,
        generator_name=combined_name,
        parameters={
            "operation": operation,
            "components": [
                {"name": s.generator_name, "params": s.parameters}
                for s in series_list
            ],
        },
    )


def _concatenate_series(series_list: tuple[TimeSeries, ...]) -> TimeSeries:
    """Concatenate time series end-to-end."""
    data_parts = [s.data for s in series_list]
    data = np.concatenate(data_parts)

    # Adjust change point indices for concatenated series
    all_change_points = []
    offset = 0

    for s in series_list:
        for cp in s.change_points:
            adjusted_cp = ChangePoint(
                index=cp.index + offset,
                change_type=cp.change_type,
                before_value=cp.before_value,
                after_value=cp.after_value,
                description=cp.description,
            )
            all_change_points.append(adjusted_cp)
        offset += len(s)

    generator_names = [s.generator_name for s in series_list]
    combined_name = f"concatenate({', '.join(generator_names)})"

    return TimeSeries(
        data=data,
        change_points=all_change_points,
        generator_name=combined_name,
        parameters={
            "operation": "concatenate",
            "components": [
                {"name": s.generator_name, "params": s.parameters}
                for s in series_list
            ],
        },
    )


def add_noise(
    series: TimeSeries,
    sigma: float = 5.0,
    distribution: str = "normal",
    seed: int | None = None,
) -> TimeSeries:
    """
    Add noise to an existing time series.

    Convenience function to add realistic noise to any pattern.

    Args:
        series: The base time series.
        sigma: Standard deviation (for normal) or half-range (for uniform).
        distribution: "normal" or "uniform".
        seed: Random seed for reproducibility.

    Returns:
        New TimeSeries with noise added.
    """
    rng = np.random.default_rng(seed)

    if distribution == "normal":
        noise = rng.normal(0, sigma, len(series))
    elif distribution == "uniform":
        noise = rng.uniform(-sigma, sigma, len(series))
    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    data = series.data + noise

    return TimeSeries(
        data=data,
        change_points=series.change_points.copy(),
        generator_name=f"{series.generator_name}+noise_{distribution}",
        parameters={
            "base": {"name": series.generator_name, "params": series.parameters},
            "noise_sigma": sigma,
            "noise_distribution": distribution,
            "seed": seed,
        },
    )


class CombinationGenerator:
    """
    Generator for creating all combinations of building block time series.

    This class systematically generates combinations of basic patterns
    for comprehensive testing of change point detection algorithms.
    """

    def __init__(
        self,
        lengths: list[int] | None = None,
        seed: int | None = None,
    ):
        """
        Initialize the combination generator.

        Args:
            lengths: List of time series lengths to generate.
                    Defaults to [50, 500] per spec.
            seed: Base random seed for reproducibility.
        """
        self.lengths = lengths or [50, 500]
        self.seed = seed

    def generate_basic_blocks(self) -> list[tuple[str, Callable[..., TimeSeries]]]:
        """
        Get list of basic building block generators.

        Returns:
            List of (name, generator_function) tuples.
        """
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

        return [
            ("constant", constant),
            ("noise_normal", noise_normal),
            ("noise_uniform", noise_uniform),
            ("outlier", outlier),
            ("step_function", step_function),
            ("regression_fix", regression_fix),
            ("banding", banding),
            ("variance_change", variance_change),
            ("phase_change", phase_change),
            ("multiple_changes", multiple_changes),
        ]

    def generate_all_basic(self) -> dict[str, list[TimeSeries]]:
        """
        Generate all basic time series for each length.

        Returns:
            Dictionary mapping generator name to list of TimeSeries
            (one per length).
        """
        results = {}

        for name, gen_func in self.generate_basic_blocks():
            series_list = []
            for length in self.lengths:
                try:
                    ts = gen_func(length=length, seed=self.seed)
                    series_list.append(ts)
                except Exception as e:
                    print(f"Warning: Could not generate {name} with length={length}: {e}")
            results[name] = series_list

        return results

    def generate_with_noise_variants(
        self,
        sigmas: list[float] | None = None,
    ) -> list[TimeSeries]:
        """
        Generate all basic patterns, each with different noise levels.

        Args:
            sigmas: List of noise standard deviations to apply.
                   Defaults to [0, 2, 5, 10].

        Returns:
            List of all generated TimeSeries.
        """
        if sigmas is None:
            sigmas = [0.0, 2.0, 5.0, 10.0]

        results = []
        basic = self.generate_all_basic()

        for name, series_list in basic.items():
            for ts in series_list:
                for sigma in sigmas:
                    if sigma == 0:
                        results.append(ts)
                    else:
                        noisy = add_noise(ts, sigma=sigma, seed=self.seed)
                        results.append(noisy)

        return results

    def generate_pairwise_combinations(
        self,
        add_noise_sigma: float = 5.0,
    ) -> list[TimeSeries]:
        """
        Generate all pairwise combinations of building blocks.

        For each pair of pattern types, combines them using addition.
        E.g., step_function + outlier, banding + variance_change, etc.

        Args:
            add_noise_sigma: Noise to add to combined series.

        Returns:
            List of combined TimeSeries.
        """
        from otava_test_data.generators.basic import (
            constant,
            outlier,
            step_function,
            regression_fix,
        )
        from otava_test_data.generators.advanced import (
            banding,
            variance_change,
            multiple_changes,
        )

        # Patterns that can be meaningfully combined (have change points or structure)
        combinable_patterns = [
            ("outlier", outlier),
            ("step_function", step_function),
            ("regression_fix", regression_fix),
            ("banding", banding),
            ("variance_change", variance_change),
            ("multiple_changes", multiple_changes),
        ]

        results = []

        for length in self.lengths:
            # Generate each pair combination
            for i, (name1, gen1) in enumerate(combinable_patterns):
                for name2, gen2 in combinable_patterns[i + 1:]:
                    try:
                        # Generate base patterns with zero baseline for clean combination
                        ts1 = gen1(length=length, seed=self.seed)
                        ts2 = gen2(length=length, seed=self.seed if self.seed else None)

                        # Combine and add noise
                        combined = combine(ts1, ts2, operation="add")
                        if add_noise_sigma > 0:
                            combined = add_noise(
                                combined,
                                sigma=add_noise_sigma,
                                seed=self.seed,
                            )
                        results.append(combined)
                    except Exception as e:
                        print(f"Warning: Could not combine {name1}+{name2}: {e}")

        return results

    def generate_all_test_cases(
        self,
        include_combinations: bool = True,
        noise_levels: list[float] | None = None,
    ) -> list[TimeSeries]:
        """
        Generate comprehensive set of test cases.

        This is the main entry point for generating test data for Otava.

        Args:
            include_combinations: Whether to include pairwise combinations.
            noise_levels: List of noise sigmas to apply.

        Returns:
            List of all generated TimeSeries.
        """
        all_series = []

        # Basic patterns with noise variants
        all_series.extend(self.generate_with_noise_variants(noise_levels))

        # Pairwise combinations
        if include_combinations:
            all_series.extend(self.generate_pairwise_combinations())

        return all_series


def generate_test_suite(
    output_dir: str = "test_data",
    lengths: list[int] | None = None,
    seed: int = 42,
) -> list[str]:
    """
    Generate a complete test suite and save to CSV files.

    Args:
        output_dir: Directory to save CSV files.
        lengths: Time series lengths to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of generated file paths.
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    generator = CombinationGenerator(lengths=lengths, seed=seed)
    all_series = generator.generate_all_test_cases()

    file_paths = []
    for i, ts in enumerate(all_series):
        filename = f"{output_dir}/{i:04d}_{ts.generator_name.replace('(', '_').replace(')', '_').replace(', ', '_')}_L{len(ts)}.csv"
        # Clean up filename
        filename = filename.replace("__", "_").replace("_.", ".")
        ts.to_csv(filename)
        file_paths.append(filename)

    return file_paths
