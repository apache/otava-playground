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
Tests for time series generators.

These tests verify that the generators produce correct output with
expected properties and change points.
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_allclose

from otava_test_data.generators.basic import (
    constant,
    noise_normal,
    noise_uniform,
    outlier,
    step_function,
    regression_fix,
    TimeSeries,
    ChangePoint,
)
from otava_test_data.generators.advanced import (
    banding,
    variance_change,
    phase_change,
    multiple_changes,
    multiple_outliers,
    multiple_variance_changes,
)
from otava_test_data.generators.combiner import (
    combine,
    add_noise,
    CombinationGenerator,
)


# Parameterize with spec-defined lengths
LENGTHS = [50, 500]


class TestConstant:
    """Tests for constant time series generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_constant_length(self, length: int):
        """Constant series has correct length."""
        ts = constant(length=length)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_constant_value(self, length: int):
        """All values in constant series are equal."""
        ts = constant(length=length, value=42.0)
        assert np.all(ts.data == 42.0)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_constant_no_change_points(self, length: int):
        """Constant series has no change points."""
        ts = constant(length=length)
        assert len(ts.change_points) == 0


class TestNoiseNormal:
    """Tests for normally distributed noise generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_normal_length(self, length: int):
        """Normal noise series has correct length."""
        ts = noise_normal(length=length, seed=42)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_normal_mean(self, length: int):
        """Normal noise has approximately correct mean."""
        ts = noise_normal(length=length, mean=100.0, sigma=5.0, seed=42)
        # With bounded noise, mean should be very close
        assert abs(np.mean(ts.data) - 100.0) < 3 * 5.0 / np.sqrt(length)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_normal_bounded(self, length: int):
        """Bounded normal noise stays within 4 sigma."""
        mean, sigma = 100.0, 5.0
        ts = noise_normal(length=length, mean=mean, sigma=sigma, bounded=True, seed=42)
        assert np.all(ts.data >= mean - 4 * sigma)
        assert np.all(ts.data <= mean + 4 * sigma)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_normal_no_change_points(self, length: int):
        """Normal noise series has no change points."""
        ts = noise_normal(length=length, seed=42)
        assert len(ts.change_points) == 0

    def test_noise_normal_reproducible(self):
        """Same seed produces same output."""
        ts1 = noise_normal(length=100, seed=42)
        ts2 = noise_normal(length=100, seed=42)
        assert_array_almost_equal(ts1.data, ts2.data)


class TestNoiseUniform:
    """Tests for uniformly distributed noise generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_uniform_length(self, length: int):
        """Uniform noise series has correct length."""
        ts = noise_uniform(length=length, seed=42)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_uniform_bounds(self, length: int):
        """Uniform noise stays within specified bounds."""
        min_val, max_val = 90.0, 110.0
        ts = noise_uniform(length=length, min_val=min_val, max_val=max_val, seed=42)
        assert np.all(ts.data >= min_val)
        assert np.all(ts.data <= max_val)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_noise_uniform_no_change_points(self, length: int):
        """Uniform noise series has no change points."""
        ts = noise_uniform(length=length, seed=42)
        assert len(ts.change_points) == 0


class TestOutlier:
    """Tests for single outlier generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_outlier_length(self, length: int):
        """Outlier series has correct length."""
        ts = outlier(length=length)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_outlier_position(self, length: int):
        """Outlier is at correct position."""
        idx = length // 3
        ts = outlier(length=length, baseline=100.0, outlier_value=150.0, outlier_index=idx)
        assert ts.data[idx] == 150.0
        assert ts.data[idx - 1] == 100.0
        assert ts.data[idx + 1] == 100.0

    @pytest.mark.parametrize("length", LENGTHS)
    def test_outlier_change_point(self, length: int):
        """Outlier has one change point marked."""
        ts = outlier(length=length)
        assert len(ts.change_points) == 1
        assert ts.change_points[0].change_type == "outlier"

    def test_outlier_with_noise(self):
        """Outlier still stands out with noise added."""
        ts = outlier(length=100, baseline=100.0, outlier_value=200.0, sigma=5.0, seed=42)
        idx = ts.change_points[0].index
        # Outlier should still be the maximum
        assert ts.data[idx] == 200.0  # Outlier value is exact, not affected by noise

    def test_outlier_index_validation(self):
        """Invalid outlier index raises error."""
        with pytest.raises(ValueError):
            outlier(length=100, outlier_index=100)
        with pytest.raises(ValueError):
            outlier(length=100, outlier_index=-1)


class TestStepFunction:
    """Tests for step function (single change point) generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_step_length(self, length: int):
        """Step function has correct length."""
        ts = step_function(length=length)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_step_values(self, length: int):
        """Step function has correct values before and after."""
        idx = length // 2
        ts = step_function(
            length=length, value_before=100.0, value_after=120.0, change_index=idx
        )
        assert np.all(ts.data[:idx] == 100.0)
        assert np.all(ts.data[idx:] == 120.0)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_step_change_point(self, length: int):
        """Step function has one change point."""
        ts = step_function(length=length)
        assert len(ts.change_points) == 1
        assert ts.change_points[0].change_type == "step"

    def test_step_negative_direction(self):
        """Step can go down (improvement in latency)."""
        ts = step_function(length=100, value_before=120.0, value_after=100.0)
        cp = ts.change_points[0]
        assert cp.before_value > cp.after_value


class TestRegressionFix:
    """Tests for regression + fix generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_regression_fix_length(self, length: int):
        """Regression fix series has correct length."""
        ts = regression_fix(length=length)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_regression_fix_two_change_points(self, length: int):
        """Regression fix has exactly two change points."""
        ts = regression_fix(length=length)
        assert len(ts.change_points) == 2
        assert ts.change_points[0].change_type == "regression_start"
        assert ts.change_points[1].change_type == "regression_end"

    def test_regression_fix_special_case_same_value(self):
        """Special case: x1 == x3 (fixed back to original)."""
        ts = regression_fix(
            length=100,
            value_normal=100.0,
            value_regression=130.0,
            value_fixed=100.0,  # Same as value_normal
        )
        # First and last segments should have same value
        start = ts.change_points[0].index
        end = ts.change_points[1].index
        assert ts.data[0] == ts.data[-1]

    def test_regression_fix_min_duration(self):
        """Regression must have at least 2 points."""
        with pytest.raises(ValueError):
            regression_fix(length=100, regression_duration=1)


class TestBanding:
    """Tests for banding pattern generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_banding_length(self, length: int):
        """Banding series has correct length."""
        ts = banding(length=length, seed=42)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_banding_only_two_values(self, length: int):
        """Banding without noise has only two distinct values."""
        ts = banding(length=length, value1=100.0, value2=105.0, sigma=0.0, seed=42)
        unique_values = np.unique(ts.data)
        assert len(unique_values) == 2
        assert set(unique_values) == {100.0, 105.0}

    @pytest.mark.parametrize("length", LENGTHS)
    def test_banding_no_change_points(self, length: int):
        """Banding has no explicit change points (it's noise)."""
        ts = banding(length=length, seed=42)
        assert len(ts.change_points) == 0


class TestVarianceChange:
    """Tests for variance change generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_variance_change_length(self, length: int):
        """Variance change series has correct length."""
        ts = variance_change(length=length, seed=42)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_variance_change_one_change_point(self, length: int):
        """Variance change has one change point."""
        ts = variance_change(length=length, seed=42)
        assert len(ts.change_points) == 1
        assert ts.change_points[0].change_type == "variance"

    def test_variance_change_detectable(self):
        """Variance change is statistically detectable."""
        ts = variance_change(
            length=500,
            mean=100.0,
            sigma_before=2.0,
            sigma_after=10.0,
            change_index=250,
            seed=42,
        )
        std_before = np.std(ts.data[:250])
        std_after = np.std(ts.data[250:])
        # After should have higher variance
        assert std_after > std_before * 2


class TestPhaseChange:
    """Tests for phase change generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_phase_change_length(self, length: int):
        """Phase change series has correct length."""
        ts = phase_change(length=length, seed=42)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_phase_change_one_change_point(self, length: int):
        """Phase change has one change point."""
        ts = phase_change(length=length, seed=42)
        assert len(ts.change_points) == 1
        assert ts.change_points[0].change_type == "phase"


class TestMultipleChanges:
    """Tests for multiple consecutive changes generator."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_multiple_changes_length(self, length: int):
        """Multiple changes series has correct length."""
        ts = multiple_changes(length=length)
        assert len(ts) == length

    @pytest.mark.parametrize("length", LENGTHS)
    def test_multiple_changes_default_three(self, length: int):
        """Default multiple changes has three change points (4 values)."""
        ts = multiple_changes(length=length)
        assert len(ts.change_points) == 3

    def test_multiple_changes_custom_values(self):
        """Custom values create correct number of change points."""
        values = [100, 110, 120, 130, 140]  # 5 values = 4 changes
        ts = multiple_changes(length=500, values=values)
        assert len(ts.change_points) == 4


class TestCombine:
    """Tests for time series combination functions."""

    def test_combine_add(self):
        """Combining with addition works correctly."""
        ts1 = constant(length=100, value=100.0)
        ts2 = constant(length=100, value=10.0)
        combined = combine(ts1, ts2, operation="add")
        assert np.all(combined.data == 110.0)

    def test_combine_merges_change_points(self):
        """Combining merges change points from all series."""
        ts1 = step_function(length=100, change_index=30)
        ts2 = outlier(length=100, outlier_index=70)
        combined = combine(ts1, ts2, operation="add")
        assert len(combined.change_points) == 2

    def test_combine_requires_same_length(self):
        """Combining series of different lengths raises error."""
        ts1 = constant(length=100)
        ts2 = constant(length=200)
        with pytest.raises(ValueError):
            combine(ts1, ts2)

    def test_add_noise_function(self):
        """add_noise helper adds noise correctly."""
        ts = constant(length=100, value=100.0)
        noisy = add_noise(ts, sigma=5.0, seed=42)
        assert not np.all(noisy.data == 100.0)  # Not constant anymore
        assert abs(np.mean(noisy.data) - 100.0) < 2.0  # Mean still near 100


class TestCombinationGenerator:
    """Tests for the combination generator class."""

    def test_generate_all_basic(self):
        """Generator produces all basic patterns."""
        gen = CombinationGenerator(lengths=[50], seed=42)
        results = gen.generate_all_basic()
        # Should have all 10 basic generators
        assert len(results) >= 10

    def test_generate_with_noise_variants(self):
        """Generator produces noise variants."""
        gen = CombinationGenerator(lengths=[50], seed=42)
        results = gen.generate_with_noise_variants(sigmas=[0.0, 5.0])
        # Should have multiple variants
        assert len(results) > 10

    def test_generate_pairwise_combinations(self):
        """Generator produces pairwise combinations."""
        gen = CombinationGenerator(lengths=[50], seed=42)
        results = gen.generate_pairwise_combinations()
        # Should have combinations of 6 patterns = 6*5/2 = 15
        assert len(results) >= 10


class TestTimeSeries:
    """Tests for TimeSeries dataclass."""

    def test_to_csv(self, tmp_path):
        """TimeSeries can be exported to CSV."""
        ts = step_function(length=100)
        filepath = tmp_path / "test.csv"
        ts.to_csv(str(filepath))
        assert filepath.exists()

        # Verify content
        import pandas as pd
        df = pd.read_csv(filepath)
        assert len(df) == 100
        assert "value" in df.columns
        assert "is_change_point" in df.columns

    def test_get_change_point_indices(self):
        """get_change_point_indices returns correct indices."""
        ts = regression_fix(length=100, regression_start=30, regression_duration=20)
        indices = ts.get_change_point_indices()
        assert indices == [30, 50]
