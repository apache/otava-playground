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
Integration tests with Apache Otava.

These tests verify that Otava can correctly detect change points
in the generated test data.
"""

import pytest
import tempfile
import os
from pathlib import Path

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
    multiple_changes,
)
from otava_test_data.generators.combiner import add_noise, CombinationGenerator

# Check if Otava is available
try:
    import otava
    OTAVA_AVAILABLE = True
except ImportError:
    OTAVA_AVAILABLE = False

# Standard test lengths from spec
LENGTHS = [50, 500]

# Markers for tests requiring Otava
otava_required = pytest.mark.skipif(
    not OTAVA_AVAILABLE,
    reason="Apache Otava not installed"
)


def prepare_csv_for_otava(ts, tmp_path: Path) -> str:
    """
    Prepare a CSV file in format Otava expects.

    Otava expects CSV with time series data. The exact format depends
    on Otava's configuration.

    Args:
        ts: TimeSeries object
        tmp_path: Temporary directory path

    Returns:
        Path to the CSV file
    """
    filepath = tmp_path / f"{ts.generator_name}_{len(ts)}.csv"
    ts.to_csv(str(filepath), include_metadata=False)
    return str(filepath)


@otava_required
class TestOtavaConstant:
    """Test Otava behavior on constant time series (no change points expected)."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_constant_no_detection(self, length: int, tmp_path):
        """Otava should detect no change points in constant data."""
        ts = constant(length=length, value=100.0)
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Implement actual Otava invocation
        # This will depend on Otava's API/CLI interface
        # For now, this is a placeholder
        assert os.path.exists(csv_path)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_constant_with_noise_no_detection(self, length: int, tmp_path):
        """Otava should detect no change points in noisy constant data."""
        ts = noise_normal(length=length, mean=100.0, sigma=5.0, seed=42)
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Implement actual Otava invocation
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaStepFunction:
    """Test Otava detection of step functions (single change point)."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_step_detected(self, length: int, tmp_path):
        """Otava should detect the step change point."""
        ts = step_function(
            length=length,
            value_before=100.0,
            value_after=120.0,
            change_index=length // 2,
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # Expected change point
        expected_cp = length // 2

        # TODO: Invoke Otava and verify it detects change near expected_cp
        assert os.path.exists(csv_path)
        assert len(ts.change_points) == 1

    @pytest.mark.parametrize("length", LENGTHS)
    @pytest.mark.parametrize("step_size", [5, 10, 20, 50])
    def test_step_various_sizes(self, length: int, step_size: int, tmp_path):
        """Otava should detect steps of various sizes."""
        ts = step_function(
            length=length,
            value_before=100.0,
            value_after=100.0 + step_size,
            sigma=2.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Invoke Otava - larger steps should be easier to detect
        assert os.path.exists(csv_path)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_step_down_detected(self, length: int, tmp_path):
        """Otava should detect downward steps (improvements)."""
        ts = step_function(
            length=length,
            value_before=120.0,
            value_after=100.0,  # Improvement
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Invoke Otava
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaOutlier:
    """Test Otava behavior on outliers (single anomalous points)."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_outlier_handling(self, length: int, tmp_path):
        """
        Test how Otava handles single outliers.

        Note: A single outlier may or may not be detected as a change point
        depending on algorithm design. Some algorithms filter outliers,
        others may briefly detect them.
        """
        ts = outlier(
            length=length,
            baseline=100.0,
            outlier_value=150.0,
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Invoke Otava and document behavior
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaRegressionFix:
    """Test Otava detection of regression + fix patterns."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_regression_fix_two_changes(self, length: int, tmp_path):
        """Otava should detect both change points in regression+fix."""
        ts = regression_fix(
            length=length,
            value_normal=100.0,
            value_regression=130.0,
            value_fixed=100.0,
            regression_duration=max(10, length // 10),
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # Expected: 2 change points
        assert len(ts.change_points) == 2

        # TODO: Invoke Otava and verify both changes detected
        assert os.path.exists(csv_path)

    @pytest.mark.parametrize("length", LENGTHS)
    @pytest.mark.parametrize("duration", [2, 5, 10, 20])
    def test_regression_various_durations(self, length: int, duration: int, tmp_path):
        """Test detection with various regression durations."""
        if duration >= length // 3:
            pytest.skip("Duration too long for this length")

        ts = regression_fix(
            length=length,
            value_normal=100.0,
            value_regression=130.0,
            regression_duration=duration,
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Short durations may be harder to detect
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaVarianceChange:
    """Test Otava detection of variance changes."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_variance_increase_detected(self, length: int, tmp_path):
        """Otava should detect when variance increases."""
        ts = variance_change(
            length=length,
            mean=100.0,
            sigma_before=2.0,
            sigma_after=10.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Otava may or may not detect variance changes
        # Document behavior
        assert os.path.exists(csv_path)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_variance_decrease_detected(self, length: int, tmp_path):
        """Otava should detect when variance decreases."""
        ts = variance_change(
            length=length,
            mean=100.0,
            sigma_before=10.0,
            sigma_after=2.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Invoke Otava
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaMultipleChanges:
    """Test Otava detection of multiple consecutive changes."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_multiple_changes_all_detected(self, length: int, tmp_path):
        """Otava should detect all change points."""
        ts = multiple_changes(
            length=length,
            values=[100.0, 110.0, 120.0, 130.0],
            sigma=5.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # Expected: 3 change points
        assert len(ts.change_points) == 3

        # TODO: Invoke Otava and check all detected
        assert os.path.exists(csv_path)

    @pytest.mark.parametrize("length", LENGTHS)
    def test_rapid_consecutive_changes(self, length: int, tmp_path):
        """Test detection of rapid back-to-back changes."""
        # Changes close together
        segment = length // 10
        ts = multiple_changes(
            length=length,
            values=[100.0, 115.0, 105.0, 120.0],
            change_indices=[segment, 2 * segment, 3 * segment],
            sigma=3.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Rapid changes may be challenging
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaBanding:
    """Test Otava behavior on banding patterns."""

    @pytest.mark.parametrize("length", LENGTHS)
    def test_banding_not_false_positive(self, length: int, tmp_path):
        """Banding should ideally not trigger false positive detections."""
        ts = banding(
            length=length,
            value1=100.0,
            value2=105.0,  # Small band gap
            sigma=2.0,
            seed=42,
        )
        csv_path = prepare_csv_for_otava(ts, tmp_path)

        # TODO: Banding is noise, should not be detected as change points
        assert os.path.exists(csv_path)


@otava_required
class TestOtavaComprehensive:
    """Comprehensive tests using the combination generator."""

    def test_all_basic_patterns(self, tmp_path):
        """Run Otava on all basic patterns."""
        gen = CombinationGenerator(lengths=[100], seed=42)
        all_series = gen.generate_all_basic()

        results = {}
        for name, series_list in all_series.items():
            for ts in series_list:
                csv_path = prepare_csv_for_otava(ts, tmp_path)
                # TODO: Run Otava and collect results
                results[f"{name}_{len(ts)}"] = {
                    "csv_path": csv_path,
                    "expected_change_points": len(ts.change_points),
                    "expected_indices": ts.get_change_point_indices(),
                }

        # Verify all files created
        assert len(results) >= 10

    def test_noise_sensitivity(self, tmp_path):
        """Test detection accuracy at various noise levels."""
        noise_levels = [0.0, 2.0, 5.0, 10.0, 20.0]
        step_size = 20.0

        results = {}
        for sigma in noise_levels:
            ts = step_function(
                length=200,
                value_before=100.0,
                value_after=100.0 + step_size,
                sigma=sigma,
                seed=42,
            )
            csv_path = prepare_csv_for_otava(ts, tmp_path)

            results[f"sigma_{sigma}"] = {
                "csv_path": csv_path,
                "snr": step_size / sigma if sigma > 0 else float("inf"),
            }

        # Higher noise should make detection harder
        assert len(results) == len(noise_levels)


class TestBenchmarkData:
    """Tests for generating benchmark datasets."""

    def test_generate_benchmark_suite(self, tmp_path):
        """Generate a complete benchmark suite for algorithm comparison."""
        gen = CombinationGenerator(lengths=[50, 200], seed=42)

        # Generate test cases
        all_series = gen.generate_all_test_cases(
            include_combinations=True,
            noise_levels=[0.0, 5.0],
        )

        # Save all to CSV
        output_dir = tmp_path / "benchmark"
        output_dir.mkdir()

        manifest = []
        for i, ts in enumerate(all_series):
            filename = f"{i:04d}_{ts.generator_name[:30]}.csv"
            filepath = output_dir / filename
            ts.to_csv(str(filepath))

            manifest.append({
                "filename": filename,
                "generator": ts.generator_name,
                "length": len(ts),
                "n_change_points": len(ts.change_points),
                "change_point_indices": ts.get_change_point_indices(),
            })

        # Should have substantial test suite
        assert len(manifest) > 50

        # Write manifest
        import json
        manifest_path = output_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        assert manifest_path.exists()
