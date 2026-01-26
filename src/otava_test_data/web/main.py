"""
FastAPI web application for visualizing Otava test data.

Run with: uvicorn otava_test_data.web.main:app --reload
Or: otava-web
"""

import json
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
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
    variance_change,
    phase_change,
    multiple_changes,
    multiple_outliers,
    multiple_variance_changes,
    multiple_regression_fix,
    multiple_banding,
    multiple_phase_changes,
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

# Generator registry with metadata
GENERATORS = {
    "constant": {
        "func": constant,
        "name": "Constant",
        "description": "Constant value: S = x, x, x, x...",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "value": {"type": "float", "default": 100.0, "min": 0, "max": 1000, "step": 1},
        },
    },
    "noise_normal": {
        "func": noise_normal,
        "name": "Normal Noise",
        "description": "Normally distributed: S ~ N(mean, sigma)",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 1000, "step": 1},
            "sigma": {"type": "float", "default": 5.0, "min": 0.1, "max": 50, "step": 0.5},
        },
    },
    "noise_uniform": {
        "func": noise_uniform,
        "name": "Uniform Noise",
        "description": "Uniformly distributed (white noise): random(min, max)",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "min_val": {"type": "float", "default": 90.0, "min": 0, "max": 500, "step": 1},
            "max_val": {"type": "float", "default": 110.0, "min": 0, "max": 500, "step": 1},
        },
    },
    "outlier": {
        "func": outlier,
        "name": "Single Outlier",
        "description": "Single anomaly point: S = x, x, x', x, x...",
        "category": "basic",
        "has_change_points": False,
        "params": {
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "outlier_value": {"type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "step_function": {
        "func": step_function,
        "name": "Step Function",
        "description": "Single change point: S = x1, x1, x2, x2...",
        "category": "basic",
        "has_change_points": True,
        "params": {
            "value_before": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_after": {"type": "float", "default": 120.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "regression_fix": {
        "func": regression_fix,
        "name": "Regression + Fix",
        "description": "Temporary regression: S = x1, x2, x3...",
        "category": "basic",
        "has_change_points": True,
        "params": {
            "value_normal": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_regression": {"type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1},
            "regression_duration": {"type": "int", "default": 20, "min": 2, "max": 100, "step": 1},
            "sigma": {"type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "banding": {
        "func": banding,
        "name": "Banding",
        "description": "Oscillation between two values",
        "category": "advanced",
        "has_change_points": False,
        "params": {
            "value1": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value2": {"type": "float", "default": 105.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 2.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "variance_change": {
        "func": variance_change,
        "name": "Variance Change",
        "description": "Constant mean, changing variance",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "sigma_before": {"type": "float", "default": 2.0, "min": 0.1, "max": 30, "step": 0.5},
            "sigma_after": {"type": "float", "default": 10.0, "min": 0.1, "max": 30, "step": 0.5},
        },
    },
    "phase_change": {
        "func": phase_change,
        "name": "Phase Change",
        "description": "Phase shift: cos(x) → sin(x)",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "amplitude": {"type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1},
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "period": {"type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            "sigma": {"type": "float", "default": 2.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_changes": {
        "func": multiple_changes,
        "name": "Multiple Changes",
        "description": "Multiple consecutive step changes",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "sigma": {"type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_outliers": {
        "func": multiple_outliers,
        "name": "Multiple Outliers",
        "description": "Multiple anomalous points",
        "category": "advanced",
        "has_change_points": False,
        "params": {
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "outlier_value": {"type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1},
            "n_outliers": {"type": "int", "default": 5, "min": 2, "max": 20, "step": 1},
            "sigma": {"type": "float", "default": 5.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_variance_changes": {
        "func": multiple_variance_changes,
        "name": "Multiple Variance Changes",
        "description": "Multiple variance changes, constant mean",
        "category": "advanced",
        "has_change_points": True,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
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
            "value_before": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_after": {"type": "float", "default": 120.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_changes_clean": {
        "func": multiple_changes,
        "name": "Multiple Changes (Clean)",
        "description": "Multiple step changes without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "regression_fix_clean": {
        "func": regression_fix,
        "name": "Regression + Fix (Clean)",
        "description": "Temporary regression without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "value_normal": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value_regression": {"type": "float", "default": 130.0, "min": 0, "max": 500, "step": 1},
            "regression_duration": {"type": "int", "default": 20, "min": 2, "max": 100, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "banding_clean": {
        "func": banding,
        "name": "Banding (Clean)",
        "description": "Clean oscillation between two values",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "value1": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "value2": {"type": "float", "default": 110.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "outlier_clean": {
        "func": outlier,
        "name": "Single Outlier (Clean)",
        "description": "Clean single anomaly point without noise",
        "category": "clean",
        "has_change_points": False,
        "params": {
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "outlier_value": {"type": "float", "default": 150.0, "min": 0, "max": 500, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "variance_change_clean": {
        "func": variance_change,
        "name": "Variance Change (Clean)",
        "description": "Clean variance change pattern",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "sigma_before": {"type": "float", "default": 0.5, "min": 0.1, "max": 30, "step": 0.5},
            "sigma_after": {"type": "float", "default": 8.0, "min": 0.1, "max": 30, "step": 0.5},
        },
    },
    "phase_change_clean": {
        "func": phase_change,
        "name": "Phase Change (Clean)",
        "description": "Clean phase shift without noise",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "amplitude": {"type": "float", "default": 10.0, "min": 1, "max": 50, "step": 1},
            "baseline": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
            "period": {"type": "int", "default": 20, "min": 5, "max": 100, "step": 1},
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
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
    "multiple_variance_changes_clean": {
        "func": multiple_variance_changes,
        "name": "Multiple Variance Changes (Clean)",
        "description": "Clean multiple variance changes pattern",
        "category": "clean",
        "has_change_points": True,
        "params": {
            "mean": {"type": "float", "default": 100.0, "min": 0, "max": 500, "step": 1},
        },
    },
    "multiple_regression_fix_clean": {
        "func": multiple_regression_fix,
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
        "has_change_points": True,
        "params": {
            "sigma": {"type": "float", "default": 0.0, "min": 0, "max": 20, "step": 0.5},
        },
    },
    "multiple_phase_changes_clean": {
        "func": multiple_phase_changes,
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
    """List all available generators with metadata."""
    return {
        name: {
            "name": info["name"],
            "description": info["description"],
            "category": info["category"],
            "has_change_points": info["has_change_points"],
            "params": info["params"],
        }
        for name, info in GENERATORS.items()
    }


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
