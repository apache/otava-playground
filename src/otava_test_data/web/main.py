"""
FastAPI web application for visualizing Otava test data.

Run with: uvicorn otava_test_data.web.main:app --reload
Or: otava-web
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, Request, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Otava imports - optional dependency
try:
    from otava.analysis import compute_change_points
    OTAVA_AVAILABLE = True
except ImportError:
    OTAVA_AVAILABLE = False
    compute_change_points = None

from otava_test_data.generators.basic import (
    constant,
    noise_normal,
    noise_uniform,
    outlier,
    step_function,
    regression_fix,
    TimeSeries,
)
from otava_test_data.generators.advanced import (
    banding,
    outlier_clean,
    variance_change,
    phase_change,
    amplitude_change_clean,
    multiple_amplitude_changes_clean,
    multiple_changes,
    multiple_outliers,
    multiple_outliers_clean,
    multiple_variance_changes,
    multiple_regression_fix,
    multiple_regression_fix_clean,
    multiple_banding,
    multiple_phase_changes,
    multiple_phase_changes_clean,
    # Uniform noise variants
    outlier_uniform,
    step_function_uniform,
    regression_fix_uniform,
    banding_uniform,
    phase_change_uniform,
)
from otava_test_data.generators.combiner import add_noise, CombinationGenerator
from otava_test_data import __version__

# Paths
WEB_DIR = Path(__file__).parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def sanitize_for_json(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(item) for item in obj]
    return obj

# FastAPI app
app = FastAPI(
    title="Otava Test Data Visualizer",
    description="Visualize time series test data for Apache Otava change point detection",
    version=__version__,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Generator registry with metadata and tutorial content
GENERATORS = {
    "constant": {
        "func": constant,
        "name": "Constant",
        "description": "Constant value: S = x, x, x, x...",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "value": {
                "type": "float", "default": 100.0, "min": 0, "max": 1000, "step": 1,
                "tooltip": "The constant value for all data points",
            },
        },
        "tutorial": {
            "explanation": "Generates a perfectly stable time series where every data point "
                          "has the same value. This represents an idealized system with no "
                          "variation whatsoever.",
            "use_case": "Simulates a perfectly stable system with no changes. Useful as a "
                       "baseline to verify that change point detectors produce zero false "
                       "positives when given data with no actual changes.",
            "detection_notes": "A good detector should produce exactly zero detections on this "
                              "pattern. Any detection would be a false positive.",
        },
    },
    "noise_normal": {
        "func": noise_normal,
        "name": "Normal Noise",
        "description": "Normally distributed: S ~ N(mean, sigma)",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "mean": {
                "type": "float", "default": 100.0, "min": 0, "max": 1000, "step": 1,
                "tooltip": "The center (expected value) of the normal distribution",
            },
            "sigma": {
                "type": "float", "default": 5.0, "min": 0.1, "max": 50, "step": 0.5,
                "tooltip": "Standard deviation - controls the spread of values around the mean",
            },
        },
        "tutorial": {
            "explanation": "Generates data points drawn from a Gaussian (normal) distribution. "
                          "Values cluster around the mean with the characteristic bell curve shape. "
                          "About 68% of values fall within one sigma of the mean.",
            "use_case": "Represents typical performance metrics with random variation, like "
                       "response times, CPU usage, or throughput measurements. This is the most "
                       "common noise model in real systems.",
            "detection_notes": "Detectors should not flag normal statistical variation as changes. "
                              "Occasional outliers (values beyond 2-3 sigma) are expected and "
                              "should not trigger false positives.",
        },
    },
    "noise_uniform": {
        "func": noise_uniform,
        "name": "Uniform Noise",
        "description": "Uniformly distributed (white noise): random(min, max)",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "min_val": {
                "type": "float", "default": 90.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Lower bound - no values will be below this",
            },
            "max_val": {
                "type": "float", "default": 110.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Upper bound - no values will be above this",
            },
        },
        "tutorial": {
            "explanation": "Generates data points uniformly distributed between min and max values. "
                          "Every value in the range is equally likely. Unlike normal distribution, "
                          "there's no clustering around a central value.",
            "use_case": "Simulates systems with bounded random behavior, such as random delays "
                       "within a fixed range, or load balancing across a fixed number of servers. "
                       "Tests robustness to non-Gaussian distributions.",
            "detection_notes": "Similar to normal noise, detectors should not flag this as containing "
                              "changes. The uniform distribution tests whether algorithms assume "
                              "Gaussian noise incorrectly.",
        },
    },
    "outlier": {
        "func": outlier,
        "name": "Single Outlier",
        "description": "Single anomaly point: S = x, x, x', x, x...",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal value for most data points",
            },
            "outlier_value": {
                "type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The anomalous value at the outlier point",
            },
            "sigma": {
                "type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to all points (including the outlier)",
            },
        },
        "tutorial": {
            "explanation": "Generates stable data with a single anomalous spike or dip at the "
                          "midpoint. The outlier represents a one-time glitch rather than a "
                          "persistent change in system behavior.",
            "use_case": "Simulates one-off events like a network hiccup, garbage collection pause, "
                       "or momentary resource contention. These are transient anomalies, not "
                       "persistent changes.",
            "detection_notes": "This is NOT a change point - it's an anomaly. Change point detectors "
                              "may or may not flag it, but it tests whether algorithms distinguish "
                              "between transient spikes and persistent shifts.",
        },
    },
    "step_function": {
        "func": step_function,
        "name": "Step Function",
        "description": "Single change point: S = x1, x1, x2, x2...",
        "category": "basic",
        "has_change_points": True,
        "params": {
            "value_before": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The baseline value before the change occurs",
            },
            "value_after": {
                "type": "float", "default": 120.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The new value after the change point",
            },
            "sigma": {
                "type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to obscure the exact change point",
            },
        },
        "tutorial": {
            "explanation": "The fundamental change point pattern. Data maintains one value, then "
                          "abruptly shifts to a different value at the midpoint and stays there. "
                          "This is the 'textbook' change point that all detectors should find.",
            "use_case": "Represents a performance regression or improvement that persists: a code "
                       "deployment that changes response times, a configuration change affecting "
                       "throughput, or a hardware upgrade improving capacity.",
            "detection_notes": "This is the PRIMARY test case for change point detection. A reliable "
                              "detector must find this change point accurately. The noise level (sigma) "
                              "controls detection difficulty.",
        },
    },
    "regression_fix": {
        "func": regression_fix,
        "name": "Regression + Fix",
        "description": "Temporary regression: S = x1, x2, x3...",
        "category": "basic",
        "has_change_points": True,
        "params": {
            "value_normal": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal system value (before and after the regression)",
            },
            "value_regression": {
                "type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The degraded value during the regression period",
            },
            "regression_duration": {
                "type": "int", "default": 20, "min": 2, "max": 100, "step": 1,
                "tooltip": "How many data points the regression lasts",
            },
            "sigma": {
                "type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added throughout the series",
            },
        },
        "tutorial": {
            "explanation": "Models a temporary degradation: normal operation, followed by a period "
                          "of worse performance, then returning to normal. Contains TWO change points: "
                          "the start of the regression and the fix.",
            "use_case": "Simulates a bug introduced in one release and fixed in a subsequent release, "
                       "a temporary resource constraint, or an incident that was later resolved. "
                       "Common in continuous deployment environments.",
            "detection_notes": "Detectors should identify BOTH change points: when the regression "
                              "starts and when it's fixed. This tests the ability to detect changes "
                              "in both directions.",
        },
    },
    "banding": {
        "func": banding,
        "name": "Banding",
        "description": "Oscillation between two values",
        "category": "advanced",
        "has_change_points": False,
        "params": {
            "value1": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "First band value (alternates with value2)",
            },
            "value2": {
                "type": "float", "default": 105.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Second band value (alternates with value1)",
            },
            "sigma": {
                "type": "float", "default": 2.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to each band",
            },
        },
        "tutorial": {
            "explanation": "Creates a bimodal pattern where data alternates between two distinct "
                          "values. Each point randomly picks one of the two bands, creating a "
                          "characteristic two-stripe visual pattern.",
            "use_case": "Simulates systems that intentionally alternate between states: A/B testing "
                       "with different performance characteristics, load balancing between fast and "
                       "slow servers, or caching with distinct hit/miss response times.",
            "detection_notes": "These alternations are INTENTIONAL behavior, not changes. A good "
                              "detector should NOT flag the band transitions as change points, as "
                              "this is the system's normal operating pattern.",
        },
    },
    "multiple_banding_clean": {
        "func": multiple_banding,
        "name": "Multiple Banding (Clean)",
        "description": "Clean multiple banding segments",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "values":  {"type": "list", "default": [80, 103, 130]},
        },
    },
    "variance_change": {
        "func": variance_change,
        "name": "Variance Change",
        "description": "Constant mean, changing variance",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "mean": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The average value (stays constant throughout)",
            },
            "sigma_before": {
                "type": "float", "default": 2.0, "min": 0.1, "max": 30, "step": 0.5,
                "tooltip": "Standard deviation before the change (lower = more stable)",
            },
            "sigma_after": {
                "type": "float", "default": 10.0, "min": 0.1, "max": 30, "step": 0.5,
                "tooltip": "Standard deviation after the change (higher = more volatile)",
            },
        },
        "tutorial": {
            "explanation": "The mean stays exactly the same, but the spread (variance) changes. "
                          "Data becomes more volatile (or more stable) at the change point. "
                          "This is a subtler change than a mean shift.",
            "use_case": "Represents a system becoming less reliable without changing average "
                       "performance: response times stay the same on average but become "
                       "unpredictable, or a stabilization effort that reduces jitter.",
            "detection_notes": "Tests detection of variance changes, which are harder to spot than "
                              "mean shifts. Some detectors only look for mean changes and will miss "
                              "this. Statistical tests like F-test or Levene's test are needed.",
        },
    },
    "amplitude_change_clean": {
        "func": amplitude_change_clean,
        "name": "Amplitude Change (Clean)",
        "description": "Constant mean, changing amplitude/variance",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "amplitude": {
                "type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1,
                "tooltip": "Height of the oscillation (peak to baseline)",
            },
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Center value around which the wave oscillates",
            },
            "amplitude_change": {
                "type": "float", "default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1,
                "tooltip": "Change in amplitude: multiplier",
            },
        },
        "tutorial": {
            "explanation": "The mean stays exactly the same, but the spread (variance) changes. "
                          "Data becomes more volatile (or more stable) at the change point. "
                          "This is a subtler change than a mean shift.",
            "use_case": "Represents a system becoming less reliable without changing average "
                       "performance: response times stay the same on average but become "
                       "unpredictable, or a stabilization effort that reduces jitter.",
            "detection_notes": "Tests detection of variance changes, which are harder to spot than "
                              "mean shifts. Some detectors only look for mean changes and will miss "
                              "this. Statistical tests like F-test or Levene's test are needed.",
        },
    },
    "phase_change": {
        "func": phase_change,
        "name": "Phase Change",
        "description": "Phase shift: cos(x) → sin(x)",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "amplitude": {
                "type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1,
                "tooltip": "Height of the oscillation (peak to baseline)",
            },
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Center value around which the wave oscillates",
            },
            "period": {
                "type": "int", "default": 20, "min": 5, "max": 100, "step": 1,
                "tooltip": "How many points for one complete cycle",
            },
            "sigma": {
                "type": "float", "default": 2.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to the wave",
            },
        },
        "tutorial": {
            "explanation": "Generates a periodic (wave-like) signal that changes phase at the "
                          "midpoint. Before: cosine wave (starts at peak). After: sine wave "
                          "(starts at zero). Mean and variance remain the same.",
            "use_case": "Rare in performance data, but tests edge cases. Could represent timing "
                       "or synchronization changes, clock drift corrections, or periodic process "
                       "scheduling changes.",
            "detection_notes": "Extremely difficult to detect with standard methods since mean and "
                              "variance don't change. Requires frequency-domain analysis or "
                              "specialized phase detection. Most detectors will miss this.",
        },
    },
    "phase_change_clean": {
        "func": phase_change,
        "name": "Phase Change (Clean)",
        "description": "Phase shift: cos(x) → sin(x)",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "amplitude": {
                "type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1,
                "tooltip": "Height of the oscillation (peak to baseline)",
            },
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Center value around which the wave oscillates",
            },
            "period": {
                "type": "int", "default": 20, "min": 5, "max": 100, "step": 1,
                "tooltip": "How many points for one complete cycle",
            },
            "sigma": {
                "type": "float", "default": 2.0, "min": 0, "max": 0, "step": 0.0,
                "tooltip": "NO Random noise added to the wave",
            },
        },
        "tutorial": {
            "explanation": "Generates a periodic (wave-like) signal that changes phase at the "
                          "midpoint. Before: cosine wave (starts at peak). After: sine wave "
                          "(starts at zero). Mean and variance remain the same.",
            "use_case": "Rare in performance data, but tests edge cases. Could represent timing "
                       "or synchronization changes, clock drift corrections, or periodic process "
                       "scheduling changes.",
            "detection_notes": "Extremely difficult to detect with standard methods since mean and "
                              "variance don't change. Requires frequency-domain analysis or "
                              "specialized phase detection. Most detectors will miss this.",
        },
    },
    "multiple_phase_changes_clean": {
        "func": multiple_phase_changes_clean,
        "name": "Multiple Phase Changes (Clean)",
        "description": "Clean multiple phase shifts",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "amplitude": {"type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1},
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "period": {"type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            "n_changes": {"type": "int", "default": 3, "min": 1, "max": 10, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_changes": {
        "func": multiple_changes,
        "name": "Multiple Changes",
        "description": "Multiple consecutive step changes",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "sigma": {
                "type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to all segments",
            },
        },
        "tutorial": {
            "explanation": "Contains multiple step changes at different points in the series. "
                          "The data transitions through several distinct levels, with each "
                          "transition being a separate change point to detect.",
            "use_case": "Represents gradual improvements or degradations over time: multiple "
                       "optimization efforts, cascading failures, or phased rollouts where each "
                       "phase affects performance differently.",
            "detection_notes": "Detectors should find ALL transition points, not just the first one. "
                              "Tests the ability to detect multiple changes and avoid 'masking' "
                              "where detecting one change prevents detecting others.",
        },
    },
    "multiple_outliers": {
        "func": multiple_outliers,
        "name": "Multiple Outliers",
        "description": "Multiple anomalous points",
        "category": "advanced",
        "has_change_points": False,
        "params": {
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal value for most data points",
            },
            "outlier_value": {
                "type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The value at anomalous points",
            },
            "n_outliers": {
                "type": "int", "default": 5, "min": 2, "max": 20, "step": 1,
                "tooltip": "Number of outlier points to generate",
            },
            "sigma": {
                "type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Random noise added to all points",
            },
        },
        "tutorial": {
            "explanation": "Generates stable data with several random spikes scattered throughout. "
                          "Each outlier is independent and the system returns to baseline immediately. "
                          "No persistent change in behavior occurs.",
            "use_case": "Simulates intermittent issues: occasional garbage collection pauses, "
                       "sporadic network timeouts, or random resource contention. These are "
                       "noise, not changes.",
            "detection_notes": "Like single outliers, these are NOT change points. Tests whether "
                              "detectors can distinguish between multiple anomalies and actual "
                              "regime changes. Should not trigger false positives.",
        },
    },
    "multiple_variance_changes": {
        "func": multiple_variance_changes,
        "name": "Multiple Variance Changes",
        "description": "Multiple variance changes, constant mean",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "mean": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The average value (stays constant throughout)",
            },
        },
        "tutorial": {
            "explanation": "The mean stays constant while variance changes multiple times. "
                          "Data alternates between stable and volatile periods, creating "
                          "multiple variance change points to detect.",
            "use_case": "Represents a system that goes through phases of stability and instability: "
                       "periodic maintenance windows, varying load conditions, or intermittent "
                       "environmental factors affecting reliability.",
            "detection_notes": "Combines the difficulty of variance detection with multiple change "
                              "points. Tests advanced detection capabilities. Many simple detectors "
                              "will fail on this pattern.",
        },
    },
    # Clean patterns (no noise) for visualization
    "step_function_clean": {
        "func": step_function,
        "name": "Step Function (Clean)",
        "description": "Clean step change without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "value_before": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The baseline value before the change occurs",
            },
            "value_after": {
                "type": "float", "default": 120.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The new value after the change point",
            },
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean signal (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "A perfect step function with no random noise. The change point is "
                          "exactly visible as an instant jump from one value to another. "
                          "Useful for understanding the basic pattern before adding noise.",
            "use_case": "Educational visualization of what a step change looks like in ideal "
                       "conditions. Also useful for testing detector behavior on trivially "
                       "easy cases.",
            "detection_notes": "Any detector should trivially find this change point. If a detector "
                              "fails on clean data, it has fundamental issues. Use this to verify "
                              "basic functionality.",
        },
    },
    "multiple_changes_clean": {
        "func": multiple_changes,
        "name": "Multiple Changes (Clean)",
        "description": "Multiple step changes without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean signal (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "Multiple step changes with no noise, showing each level transition "
                          "as a perfectly sharp boundary. The staircase pattern is immediately "
                          "visible.",
            "use_case": "Educational visualization of multiple change points. Helps understand "
                       "what detectors are looking for before noise obscures the pattern.",
            "detection_notes": "All change points should be trivially detectable. Use this to "
                              "verify that a detector can find multiple changes without being "
                              "confused by the easy case.",
        },
    },
    "regression_fix_clean": {
        "func": regression_fix,
        "name": "Regression + Fix (Clean)",
        "description": "Temporary regression without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "value_normal": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal system value (before and after the regression)",
            },
            "value_regression": {
                "type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The degraded value during the regression period",
            },
            "regression_duration": {
                "type": "int", "default": 20, "min": 2, "max": 100, "step": 1,
                "tooltip": "How many data points the regression lasts",
            },
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean signal (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "A clean visualization of a temporary regression pattern. Shows the "
                          "three distinct levels (normal, regression, normal) without any noise "
                          "obscuring the transitions.",
            "use_case": "Educational tool for understanding the regression-fix pattern. Both "
                       "change points (regression start and fix) are perfectly visible.",
            "detection_notes": "Both change points should be trivially detectable. Verify that "
                              "your detector finds exactly two change points at the correct locations.",
        },
    },
    "banding_clean": {
        "func": banding,
        "name": "Banding (Clean)",
        "description": "Clean oscillation between two values",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "value1": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "First band value",
            },
            "value2": {
                "type": "float", "default": 110.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Second band value",
            },
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean bands (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "Clean bimodal pattern showing exactly two discrete values. Each "
                          "point is exactly at value1 or value2 with no noise, making the "
                          "banding pattern maximally clear.",
            "use_case": "Educational visualization of what banding looks like. Helps understand "
                       "why this pattern should NOT trigger change point detection.",
            "detection_notes": "Even with no noise, this is NOT a change point pattern. The "
                              "alternation is intentional system behavior. Zero detections "
                              "is the correct result.",
        },
    },
    "outlier_clean": {
        "func": outlier_clean,
        "name": "Single Outlier (Clean)",
        "description": "Clean single anomaly point without noise",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal value for most data points",
            },
            "outlier_value": {
                "type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The anomalous value at the outlier point",
            },
        },
        "tutorial": {
            "explanation": "A perfectly clean baseline with a single visible spike. The outlier "
                          "is maximally obvious against the flat baseline, making it easy to "
                          "see the difference between an outlier and a change point.",
            "use_case": "Educational visualization contrasting outliers with change points. "
                       "The single spike clearly returns to baseline, demonstrating that "
                       "this is not a persistent change.",
            "detection_notes": "This is an OUTLIER, not a change point. Some detectors may flag "
                              "it, but the behavior is transient. Compare with step_function_clean "
                              "to see the difference.",
        },
    },
    "multiple_outliers_clean": {
        "func": multiple_outliers_clean,
        "name": "Multiple Outliers (Clean)",
        "description": "Many single anomaly points without noise",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal value for most data points",
            },
            "outlier_value": {
                "type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The anomalous value at the outlier point",
            },
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean signal (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "A perfectly clean baseline with a single visible spike. The outlier "
                          "is maximally obvious against the flat baseline, making it easy to "
                          "see the difference between an outlier and a change point.",
            "use_case": "Educational visualization contrasting outliers with change points. "
                       "The single spike clearly returns to baseline, demonstrating that "
                       "this is not a persistent change.",
            "detection_notes": "This is an OUTLIER, not a change point. Some detectors may flag "
                              "it, but the behavior is transient. Compare with step_function_clean "
                              "to see the difference.",
        },
    },
    "multiple_regression_fix_clean": {
        "func": multiple_regression_fix_clean,
        "name": "Multiple Regression + Fix (Clean)",
        "description": "Temporary regression without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "value_normal": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The normal system value (before and after the regression)",
            },
            "value_regression": {
                "type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "The degraded value during the regression period",
            },
            "regression_duration": {
                "type": "int", "default": 20, "min": 2, "max": 100, "step": 1,
                "tooltip": "How many data points the regression lasts",
            },
            "sigma": {
                "type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5,
                "tooltip": "Set to 0 for perfectly clean signal (increase to add noise)",
            },
        },
        "tutorial": {
            "explanation": "A clean visualization of a temporary regression pattern. Shows the "
                          "three distinct levels (normal, regression, normal) without any noise "
                          "obscuring the transitions.",
            "use_case": "Educational tool for understanding the regression-fix pattern. Both "
                       "change points (regression start and fix) are perfectly visible.",
            "detection_notes": "Both change points should be trivially detectable. Verify that "
                              "your detector finds exactly two change points at the correct locations.",
        },
    },
    "multiple_amplitude_changes_clean": {
        "func": multiple_amplitude_changes_clean,
        "name": "Multiple Amplitude Changes (Clean)",
        "description": "Multiple amplitude/variance changes, constant mean, zero noise",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "amplitude": {
                "type": "float", "default": 10.0, "min": 1, "max": 100, "step": 1,
                "tooltip": "Height of the oscillation (peak to baseline)",
            },
            "baseline": {
                "type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1,
                "tooltip": "Center value around which the wave oscillates",
            },
            "period": {
                "type": "int", "default": 20, "min": 5, "max": 100, "step": 1,
                "tooltip": "How many points for one complete cycle",
            },
        },
        "tutorial": {
            "explanation": "The mean stays constant while variance changes multiple times. "
                          "Data alternates between stable and volatile periods, creating "
                          "multiple variance change points to detect.",
            "use_case": "Represents a system that goes through phases of stability and instability: "
                       "periodic maintenance windows, varying load conditions, or intermittent "
                       "environmental factors affecting reliability.",
            "detection_notes": "Combines the difficulty of variance detection with multiple change "
                              "points. Tests advanced detection capabilities. Many simple detectors "
                              "will fail on this pattern.",
        }
    },
            # Uniform noise variants (Row 4)
    "outlier_uniform": {
        "func": outlier_uniform,
        "name": "Single Outlier (Uniform)",
        "description": "Single outlier with uniform noise",
        "category": "uniform",
        "has_change_points": False,
        "params": {
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "outlier_value": {"type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1},
            "noise_range": {"type": "float", "default": 10.0, "min": 0, "max": 50, "step": 1},
        },
    },
    "step_function_uniform": {
        "func": step_function_uniform,
        "name": "Step Function (Uniform)",
        "description": "Step change with uniform noise",
        "category": "uniform",
        "has_change_points": True,
        "params": {
            "value_before": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_after": {"type": "float", "default": 120.0, "min": 0, "max": 500, "step": 1},
            "noise_range": {"type": "float", "default": 10.0, "min": 0, "max": 50, "step": 1},
        },
    },
    "regression_fix_uniform": {
        "func": regression_fix_uniform,
        "name": "Regression + Fix (Uniform)",
        "description": "Regression pattern with uniform noise",
        "category": "uniform",
        "has_change_points": True,
        "params": {
            "value_normal": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_regression": {"type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1},
            "regression_duration": {"type": "int", "default": 20, "min": 2, "max": 100, "step": 1},
            "noise_range": {"type": "float", "default": 10.0, "min": 0, "max": 50, "step": 1},
        },
    },
    "variance_change_uniform": {
        "func": variance_change,
        "name": "Variance Change (Uniform)",
        "description": "Variance change (inherent variance pattern)",
        "category": "uniform",
        "has_change_points": True,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "sigma_before": {"type": "float", "default": 2.0, "min": 0.1, "max": 30, "step": 0.5},
            "sigma_after": {"type": "float", "default": 10.0, "min": 0.1, "max": 30, "step": 0.5},
        },
    },
    "phase_change_uniform": {
        "func": phase_change_uniform,
        "name": "Phase Change (Uniform)",
        "description": "Phase shift with uniform noise",
        "category": "uniform",
        "has_change_points": True,
        "params": {
            "amplitude": {"type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1},
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "period": {"type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            "noise_range": {"type": "float", "default": 4.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "banding_uniform": {
        "func": banding_uniform,
        "name": "Banding (Uniform)",
        "description": "Banding with uniform noise",
        "category": "uniform",
        "has_change_points": False,
        "params": {
            "value1": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value2": {"type": "float", "default": 110.0, "min": 0, "max": 500, "step": 1},
            "noise_range": {"type": "float", "default": 4.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
}

# Analysis method explanations for tutorial
ANALYSIS_METHODS = {
    "otava": {
        "id": "otava",
        "name": "Otava Statistical Analysis",
        "short_desc": "Statistical hypothesis testing for change detection",
        "explanation": "Apache Otava uses statistical hypothesis testing to detect change points. "
                      "It slides a window across the data and compares the distributions of values "
                      "before and after each potential change point using statistical tests.",
        "algorithm": (
            "1. Slide a window of length W across the time series\n"
            "2. At each position, split data into 'before' and 'after' segments\n"
            "3. Apply statistical tests (t-test, Kolmogorov-Smirnov) to compare distributions\n"
            "4. Calculate p-value for the null hypothesis (no change)\n"
            "5. If p-value < threshold, flag as potential change point\n"
            "6. Apply filtering to remove redundant detections"
        ),
        "best_for": [
            "Mean shifts (step functions)",
            "Variance changes",
            "Distribution changes",
            "Statistically rigorous detection",
        ],
        "limitations": [
            "Requires sufficient data on both sides of change point",
            "Window size affects sensitivity vs. precision tradeoff",
            "May miss very gradual changes",
        ],
        "parameters": {
            "window_len": {
                "name": "Window Length",
                "tooltip": "Minimum number of points on each side of a potential change point. "
                          "Larger windows give more statistical power but may miss changes near "
                          "the edges. Typical range: 10-50.",
            },
            "max_pvalue": {
                "name": "Max P-Value",
                "tooltip": "Significance threshold for detecting changes. Lower values mean "
                          "stricter detection (fewer false positives but may miss subtle changes). "
                          "0.05 is standard; use 0.01 for high confidence.",
            },
        },
    },
    "moving_average": {
        "id": "moving_average",
        "name": "Moving Average Analysis",
        "short_desc": "Rolling window mean comparison",
        "explanation": "Computes the rolling average over a sliding window and compares the mean "
                      "values before and after each point. A change is detected when the difference "
                      "between adjacent windows exceeds a threshold based on local standard deviation.",
        "algorithm": (
            "1. For each point i, compute mean of window before (W points)\n"
            "2. Compute mean of window after (W points)\n"
            "3. Calculate local standard deviation for both windows\n"
            "4. If |mean_after - mean_before| > threshold * local_std, flag as change\n"
            "5. Select local maxima to avoid detecting the same change multiple times"
        ),
        "best_for": [
            "Quick detection of sudden changes",
            "Noisy data where statistical tests may be unstable",
            "Real-time monitoring scenarios",
            "Simple, interpretable results",
        ],
        "limitations": [
            "Less statistically rigorous than hypothesis testing",
            "Threshold selection is somewhat arbitrary",
            "May be sensitive to outliers",
        ],
        "parameters": {
            "ma_window": {
                "name": "MA Window",
                "tooltip": "Size of the rolling window for computing averages. Larger windows "
                          "smooth out noise but may delay detection. Typical range: 5-20.",
            },
            "ma_threshold": {
                "name": "Threshold (sigma)",
                "tooltip": "How many standard deviations the mean difference must exceed to "
                          "trigger detection. Higher values reduce false positives. Typical: 2.0-3.0.",
            },
        },
    },
    "boundary": {
        "id": "boundary",
        "name": "Boundary Analysis",
        "short_desc": "Threshold violation detection",
        "explanation": "Simple threshold-based detection that flags points where values cross "
                      "predefined upper or lower boundaries. Each boundary crossing is detected "
                      "only once (not every point outside the bounds).",
        "algorithm": (
            "1. Define upper and lower threshold values\n"
            "2. Scan through data points sequentially\n"
            "3. When a value crosses above the upper bound (and wasn't already above), flag it\n"
            "4. When a value crosses below the lower bound (and wasn't already below), flag it\n"
            "5. Return all boundary crossing points"
        ),
        "best_for": [
            "SLA monitoring (response time limits)",
            "Known acceptable performance ranges",
            "Simple alerting systems",
            "When domain knowledge defines clear thresholds",
        ],
        "limitations": [
            "Requires knowing appropriate thresholds in advance",
            "Cannot detect changes within acceptable bounds",
            "Not adaptive to changing baseline",
            "Binary (in/out of bounds) rather than measuring change magnitude",
        ],
        "parameters": {
            "upper_bound": {
                "name": "Upper Bound",
                "tooltip": "Values crossing above this threshold will be flagged. Set based on "
                          "acceptable maximum for your metric (e.g., max response time SLA).",
            },
            "lower_bound": {
                "name": "Lower Bound",
                "tooltip": "Values crossing below this threshold will be flagged. Set based on "
                          "acceptable minimum (e.g., minimum throughput requirement).",
            },
        },
    },
}

# Detection metrics tutorial content
DETECTION_METRICS_TUTORIAL = {
    "overview": {
        "title": "Understanding Detection Metrics",
        "explanation": (
            "Change point detection is evaluated by comparing what the algorithm detected "
            "against what we know to be true (ground truth). This comparison produces metrics "
            "that tell us how well the detector is performing."
        ),
    },
    "ground_truth": {
        "title": "Ground Truth",
        "explanation": (
            "Ground truth refers to the actual, known change points in the data. In this "
            "visualizer, we generate synthetic data where we know exactly where the changes "
            "occur because we programmed them in. For example, in a step function, the ground "
            "truth is the exact index where the value jumps from 100 to 120."
        ),
        "real_world": (
            "In real-world scenarios, ground truth might come from: deployment logs (we know "
            "a release happened at time X), incident reports, or manual labeling by experts. "
            "Having accurate ground truth is essential for evaluating detector performance."
        ),
        "visual": "Shown as green dashed vertical lines on the chart.",
    },
    "true_positive": {
        "title": "True Positive (TP)",
        "explanation": (
            "A true positive occurs when the detector correctly identifies an actual change "
            "point. The detected point matches (within tolerance) a ground truth change point. "
            "This is what we want - the detector found a real change."
        ),
        "example": (
            "Ground truth has a change at index 100. The detector reports a change at index 102. "
            "With a tolerance of 5, this counts as a true positive because |102-100| <= 5."
        ),
        "visual": "Shown as blue diamonds (Otava), purple circles (MA), or cyan triangles (Boundary).",
    },
    "false_positive": {
        "title": "False Positive (FP)",
        "explanation": (
            "A false positive occurs when the detector reports a change point where none "
            "actually exists. This is a 'false alarm' - the detector thought something changed "
            "but it was just noise or normal variation."
        ),
        "example": (
            "The detector reports a change at index 150, but no ground truth change point is "
            "within tolerance of that location. This detection is incorrect."
        ),
        "visual": "Shown as red diamonds (Otava), orange circles (MA), or pink triangles (Boundary).",
        "causes": [
            "Noise in the data being mistaken for a change",
            "Threshold set too sensitive",
            "Window size too small",
            "Outliers being flagged as changes",
        ],
    },
    "false_negative": {
        "title": "False Negative (FN)",
        "explanation": (
            "A false negative occurs when the detector fails to find an actual change point. "
            "A real change exists in the ground truth, but the detector missed it. This is a "
            "'miss' - a real change went undetected."
        ),
        "example": (
            "Ground truth has a change at index 100, but the detector reports no changes nearby. "
            "The change was missed."
        ),
        "causes": [
            "Noise obscuring the change signal",
            "Threshold set too strict",
            "Window size too large (smoothing out the change)",
            "Change magnitude too small relative to noise",
        ],
    },
    "how_matching_works": {
        "title": "How Detection Matching Works",
        "explanation": (
            "To determine if a detection is a true positive or false positive, we use a "
            "tolerance-based matching algorithm:"
        ),
        "algorithm": (
            "1. For each detected change point, check if any ground truth point is within "
            "the tolerance distance\n"
            "2. If yes, it's a True Positive (and that ground truth point is marked as matched)\n"
            "3. If no ground truth point is nearby, it's a False Positive\n"
            "4. Any ground truth points not matched to any detection are False Negatives"
        ),
        "tolerance_note": (
            "The tolerance (default: 5 indices) allows for slight positional inaccuracy. "
            "Detectors often report changes slightly before or after the exact point due to "
            "the windowing algorithms they use."
        ),
    },
    "metrics": {
        "precision": {
            "title": "Precision",
            "formula": "Precision = TP / (TP + FP)",
            "explanation": (
                "Of all the changes the detector reported, what fraction were actually real? "
                "High precision means few false alarms. A precision of 100% means every "
                "detection was correct (but you might have missed some)."
            ),
        },
        "recall": {
            "title": "Recall",
            "formula": "Recall = TP / (TP + FN)",
            "explanation": (
                "Of all the real changes that exist, what fraction did the detector find? "
                "High recall means few missed changes. A recall of 100% means every real "
                "change was detected (but you might have false alarms too)."
            ),
        },
        "f1_score": {
            "title": "F1 Score",
            "formula": "F1 = 2 × (Precision × Recall) / (Precision + Recall)",
            "explanation": (
                "The harmonic mean of precision and recall, providing a single score that "
                "balances both concerns. An F1 of 100% means perfect precision AND perfect "
                "recall. It's the best single number for overall detector quality."
            ),
        },
    },
    "multiple_outliers_clean": {
        "func": multiple_outliers,
        "name": "Multiple Outliers (Clean)",
        "description": "Clean multiple anomalous points without noise",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "outlier_value": {"type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1},
            "n_outliers": {"type": "int", "default": 5, "min": 2, "max": 20, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_regression_fix_clean": {
        "func": multiple_regression_fix_clean,
        "name": "Multiple Regression + Fix (Clean)",
        "description": "Clean multiple regression+fix cycles",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "value_normal": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_regression": {"type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1},
            "n_regressions": {"type": "int", "default": 3, "min": 1, "max": 10, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_banding_clean": {
        "func": multiple_banding,
        "name": "Multiple Banding (Clean)",
        "description": "Clean multiple banding segments",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "values":  {"type": "list", "default": [80, 130]},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_phase_changes_clean": {
        "func": multiple_phase_changes_clean,
        "name": "Multiple Phase Changes (Clean)",
        "description": "Clean multiple phase shifts",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "amplitude": {"type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1},
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "period": {"type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            "n_changes": {"type": "int", "default": 3, "min": 1, "max": 10, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_changes": {
        "func": multiple_changes,
        "name": "Multiple Step Changes",
        "description": "Multiple step changes with noise",
        "category": "normal",
        "has_change_points": True,
        "params": {
            "value_normal": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_regression": {"type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1},
            "n_regressions": {"type": "int", "default": 3, "min": 1, "max": 10, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
}


def run_otava_analysis(
    data: np.ndarray,
    window_len: int = 30,
    max_pvalue: float = 0.05,
    min_magnitude: float = 0.0,
) -> dict[str, Any]:
    """
    Run Otava change point detection on data.

    Args:
        data: Time series data as numpy array.
        window_len: Minimum window length for detection.
        max_pvalue: Maximum p-value threshold for significance.
        min_magnitude: Minimum magnitude of change to report.

    Returns:
        Dictionary with detected change points and metrics.
    """
    if not OTAVA_AVAILABLE:
        return {
            "error": "apache-otava not installed. Install with: pip install otava-test-data[web]",
            "detected_change_points": [],
            "detected_indices": [],
            "count": 0,
        }

    try:
        result = compute_change_points(
            data,
            window_len=window_len,
            max_pvalue=max_pvalue,
            min_magnitude=min_magnitude,
        )

        # Result is a tuple, first element is list of ChangePoint objects
        change_points_list = result[0] if isinstance(result, tuple) else result

        detected = []
        for cp in change_points_list:
            detected.append({
                "index": int(cp.index),  # Convert numpy.int64 to int
                "mean_before": float(cp.stats.mean_1),
                "mean_after": float(cp.stats.mean_2),
                "std_before": float(cp.stats.std_1),
                "std_after": float(cp.stats.std_2),
                "pvalue": float(cp.stats.pvalue),
            })

        return {
            "detected_change_points": detected,
            "detected_indices": [cp["index"] for cp in detected],
            "count": len(detected),
            "parameters": {
                "window_len": window_len,
                "max_pvalue": max_pvalue,
                "min_magnitude": min_magnitude,
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "detected_change_points": [],
            "detected_indices": [],
            "count": 0,
        }


def compute_accuracy_metrics(
    ground_truth: list[int],
    detected: list[int],
    tolerance: int = 5,
) -> dict[str, Any]:
    """
    Compute accuracy metrics comparing detected vs ground truth change points.

    Args:
        ground_truth: List of true change point indices.
        detected: List of detected change point indices.
        tolerance: How close a detection must be to count as correct.

    Returns:
        Dictionary with accuracy metrics.
    """
    if not ground_truth and not detected:
        return {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 1.0,
            "recall": 1.0,
            "f1_score": 1.0,
            "matched_pairs": [],
        }

    if not ground_truth:
        return {
            "true_positives": 0,
            "false_positives": len(detected),
            "false_negatives": 0,
            "precision": 0.0,
            "recall": 1.0,  # No ground truth to miss
            "f1_score": 0.0,
            "matched_pairs": [],
        }

    if not detected:
        return {
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": len(ground_truth),
            "precision": 1.0,  # No false positives
            "recall": 0.0,
            "f1_score": 0.0,
            "matched_pairs": [],
        }

    # Match detected to ground truth within tolerance
    matched_truth = set()
    matched_detected = set()
    matched_pairs = []

    for d_idx in detected:
        for g_idx in ground_truth:
            if g_idx not in matched_truth and abs(d_idx - g_idx) <= tolerance:
                matched_truth.add(g_idx)
                matched_detected.add(d_idx)
                matched_pairs.append({
                    "ground_truth": int(g_idx),
                    "detected": int(d_idx),
                    "offset": int(d_idx - g_idx),
                })
                break

    true_positives = len(matched_pairs)
    false_positives = len(detected) - len(matched_detected)
    false_negatives = len(ground_truth) - len(matched_truth)

    precision = true_positives / len(detected) if detected else 1.0
    recall = true_positives / len(ground_truth) if ground_truth else 1.0
    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "matched_pairs": matched_pairs,
        "tolerance": tolerance,
    }


def timeseries_to_dict(
    ts: TimeSeries,
    include_otava: bool = False,
    otava_params: dict | None = None,
) -> dict[str, Any]:
    """Convert TimeSeries to JSON-serializable dict, optionally with Otava analysis."""
    # Convert change point indices to regular Python int to avoid numpy serialization issues
    change_point_indices = [int(i) for i in ts.get_change_point_indices()]

    result = {
        "data": ts.data.tolist(),
        "length": len(ts),
        "generator": ts.generator_name,
        "parameters": sanitize_for_json(ts.parameters),
        "ground_truth": {
            "change_points": [
                {
                    "index": int(cp.index),
                    "type": cp.change_type,
                    "before_value": float(cp.before_value) if cp.before_value is not None else None,
                    "after_value": float(cp.after_value) if cp.after_value is not None else None,
                    "description": cp.description,
                }
                for cp in ts.change_points
            ],
            "indices": change_point_indices,
            "count": len(ts.change_points),
        },
        # Keep for backward compatibility
        "change_points": [
            {
                "index": int(cp.index),
                "type": cp.change_type,
                "before_value": float(cp.before_value) if cp.before_value is not None else None,
                "after_value": float(cp.after_value) if cp.after_value is not None else None,
                "description": cp.description,
            }
            for cp in ts.change_points
        ],
        "change_point_indices": change_point_indices,
    }

    if include_otava:
        params = otava_params or {}
        otava_result = run_otava_analysis(
            ts.data,
            window_len=params.get("window_len", 30),
            max_pvalue=params.get("max_pvalue", 0.05),
            min_magnitude=params.get("min_magnitude", 0.0),
        )
        result["otava"] = otava_result

        # Compute accuracy metrics (exclude outliers - they're anomalies, not change points)
        ground_truth_indices = [
            cp.index for cp in ts.change_points if cp.change_type != "outlier"
        ]
        detected_indices = otava_result.get("detected_indices", [])
        result["accuracy"] = compute_accuracy_metrics(
            ground_truth_indices,
            detected_indices,
            tolerance=params.get("tolerance", 5),
        )

    return result


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page with generator visualization."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "generators": GENERATORS,
            "default_length": 200,
            "version": __version__,
        },
    )


@app.get("/api/generators")
async def list_generators():
    """List all available generators with metadata and tutorial content."""
    return {
        name: {
            "name": info["name"],
            "description": info["description"],
            "category": info["category"],
            "has_change_points": info["has_change_points"],
            "params": info["params"],
            "tutorial": info.get("tutorial"),
        }
        for name, info in GENERATORS.items()
    }


@app.get("/api/methods")
async def list_methods():
    """List all available analysis methods with explanations."""
    return ANALYSIS_METHODS


@app.get("/api/metrics-tutorial")
async def get_metrics_tutorial():
    """Get tutorial content explaining detection metrics."""
    return DETECTION_METRICS_TUTORIAL


@app.get("/api/generate/{generator_name}")
async def generate_data(
    generator_name: str,
    length: int = Query(default=200, ge=10, le=2000),
    seed: int = Query(default=42),
    run_otava: bool = Query(default=False, description="Run Otava analysis"),
    window_len: int = Query(default=30, ge=5, le=100, description="Otava window length"),
    max_pvalue: float = Query(default=0.00001, ge=0.0, le=1.0, description="Otava max p-value"),
    tolerance: int = Query(default=5, ge=0, le=50, description="Accuracy tolerance"),
    # Dynamic params will be passed as query parameters
    request: Request = None,
):
    """Generate time series data for a specific generator."""
    if generator_name not in GENERATORS:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unknown generator: {generator_name}"},
        )

    gen_info = GENERATORS[generator_name]
    gen_func = gen_info["func"]

    # Build kwargs from query params
    kwargs = {"length": length, "seed": seed}

    # Get additional params from query string
    query_params = dict(request.query_params)
    for param_name, param_info in gen_info["params"].items():
        if param_name in query_params:
            value = query_params[param_name]
            if param_info["type"] == "int":
                kwargs[param_name] = int(value)
            elif param_info["type"] == "float":
                kwargs[param_name] = float(value)
            else:
                kwargs[param_name] = value
        elif "default" in param_info:
            kwargs[param_name] = param_info["default"]

    try:
        ts = gen_func(**kwargs)
        otava_params = {
            "window_len": window_len,
            "max_pvalue": max_pvalue,
            "tolerance": tolerance,
        }
        return timeseries_to_dict(ts, include_otava=run_otava, otava_params=otava_params)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.get("/api/analyze/{generator_name}")
async def analyze_with_otava(
    generator_name: str,
    length: int = Query(default=200, ge=10, le=2000),
    seed: int = Query(default=42),
    window_len: int = Query(default=30, ge=5, le=100, description="Otava window length"),
    max_pvalue: float = Query(default=0.00001, ge=0.0, le=1.0, description="Otava max p-value"),
    min_magnitude: float = Query(default=0.0, ge=0, description="Minimum change magnitude"),
    tolerance: int = Query(default=5, ge=0, le=50, description="Accuracy tolerance"),
    request: Request = None,
):
    """Generate data and run Otava analysis, returning comparison results."""
    if generator_name not in GENERATORS:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unknown generator: {generator_name}"},
        )

    gen_info = GENERATORS[generator_name]
    gen_func = gen_info["func"]

    # Build kwargs from query params
    kwargs = {"length": length, "seed": seed}

    # Get additional params from query string
    query_params = dict(request.query_params)
    for param_name, param_info in gen_info["params"].items():
        if param_name in query_params:
            value = query_params[param_name]
            if param_info["type"] == "int":
                kwargs[param_name] = int(value)
            elif param_info["type"] == "float":
                kwargs[param_name] = float(value)
            else:
                kwargs[param_name] = value
        elif "default" in param_info:
            kwargs[param_name] = param_info["default"]

    try:
        ts = gen_func(**kwargs)
        otava_params = {
            "window_len": window_len,
            "max_pvalue": max_pvalue,
            "min_magnitude": min_magnitude,
            "tolerance": tolerance,
        }
        return timeseries_to_dict(ts, include_otava=True, otava_params=otava_params)
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


@app.get("/api/generate-all")
async def generate_all(
    length: int = Query(default=200, ge=10, le=2000),
    seed: int = Query(default=42),
    add_noise_sigma: float = Query(default=5.0, ge=0, le=50),
):
    """Generate all test patterns for comparison."""
    results = {}

    for name, info in GENERATORS.items():
        gen_func = info["func"]
        kwargs = {"length": length, "seed": seed}

        # Add default params
        for param_name, param_info in info["params"].items():
            if "default" in param_info:
                kwargs[param_name] = param_info["default"]

        try:
            ts = gen_func(**kwargs)
            results[name] = timeseries_to_dict(ts)
        except Exception as e:
            results[name] = {"error": str(e)}

    return results


@app.get("/api/benchmark-suite")
async def get_benchmark_suite(
    lengths: str = Query(default="50,200"),
    seed: int = Query(default=42),
):
    """Generate a complete benchmark suite."""
    length_list = [int(x.strip()) for x in lengths.split(",")]

    generator = CombinationGenerator(lengths=length_list, seed=seed)
    all_series = generator.generate_all_test_cases(
        include_combinations=False,  # Keep it simpler for web view
        noise_levels=[0.0, 5.0],
    )

    return {
        "total": len(all_series),
        "lengths": length_list,
        "seed": seed,
        "series": [timeseries_to_dict(ts) for ts in all_series[:50]],  # Limit for web
    }


class DetectRequest(BaseModel):
    """Request body for change point detection."""
    data: list[float]


@app.post("/api/detect")
async def detect_change_points(
    request: DetectRequest,
    window_len: int = Query(default=30, ge=5, le=100, description="Otava window length"),
    max_pvalue: float = Query(default=0.00001, ge=0.0, le=1.0, description="Otava max p-value"),
    min_magnitude: float = Query(default=0.0, ge=0, description="Minimum change magnitude"),
):
    """Run Otava change point detection on arbitrary data."""
    if not request.data:
        return JSONResponse(
            status_code=400,
            content={"error": "No data provided"},
        )

    try:
        data_array = np.array(request.data)
        result = run_otava_analysis(
            data_array,
            window_len=window_len,
            max_pvalue=max_pvalue,
            min_magnitude=min_magnitude,
        )
        return result
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)},
        )


def run():
    """Run the web server."""
    import uvicorn
    uvicorn.run(
        "otava_test_data.web.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
