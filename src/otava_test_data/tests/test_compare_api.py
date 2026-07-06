# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Tests for the /api/datasets and /api/compare endpoints."""

import pytest
from fastapi.testclient import TestClient

from otava_test_data.web.main import app

client = TestClient(app)


def test_list_datasets():
    r = client.get("/api/datasets")
    assert r.status_code == 200
    body = r.json()
    assert "datasets" in body
    names = [d["name"] for d in body["datasets"]]
    assert "tigerbeetle" in names


def test_get_tigerbeetle():
    r = client.get("/api/datasets/tigerbeetle")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "tigerbeetle"
    assert len(body["series"]) == 365


def test_get_unknown_dataset_404():
    r = client.get("/api/datasets/nope")
    assert r.status_code == 404


def test_list_algorithms_includes_split():
    r = client.get("/api/algorithms")
    assert r.status_code == 200
    body = r.json()
    assert "split" in body["algorithms"]
    # split must be available because apache-otava is a hard dependency.
    assert body["algorithms"]["split"]["available"] is True


def test_compare_runs_split_on_tigerbeetle():
    series = client.get("/api/datasets/tigerbeetle").json()["series"]
    r = client.post(
        "/api/compare?max_pvalue=0.001",
        json={"data": series, "algorithms": ["split"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "split" in body["results"]
    assert "indices" in body["results"]["split"]
    # TigerBeetle has clear change points — split should detect at least one.
    assert body["results"]["split"]["indices"]


def test_compare_rejects_empty_data():
    r = client.post("/api/compare", json={"data": [], "algorithms": ["split"]})
    assert r.status_code == 400


def test_compare_rejects_unknown_algorithm():
    """Unknown algorithm names should fail validation, not return 200 with an inline error."""
    r = client.post(
        "/api/compare",
        json={"data": [1.0, 2.0, 1.0, 2.0, 1.0, 2.0], "algorithms": ["nonexistent"]},
    )
    assert r.status_code == 422


def test_compare_default_runs_all_available_algorithms():
    """When `algorithms` is omitted, every available algorithm in ALGORITHMS runs."""
    available = {
        name for name, info in client.get("/api/algorithms").json()["algorithms"].items()
        if info["available"]
    }
    r = client.post(
        "/api/compare",
        json={"data": [1.0, 1.1, 1.0, 1.2, 5.0, 5.1, 5.0, 5.2, 5.3, 5.1]},
    )
    assert r.status_code == 200
    assert set(r.json()["results"].keys()) == available


def test_compare_accepts_floats_and_round_trips_through_json():
    """Float series shouldn't blow up at JSON serialization."""
    series = [1.5, 2.5, 1.7, 2.3, 1.4, 3.9, 4.1, 4.0, 4.2, 4.3, 4.1]
    r = client.post("/api/compare", json={"data": series, "algorithms": ["split"]})
    assert r.status_code == 200
    body = r.json()
    # Indices must be JSON-serializable plain ints, not numpy types.
    for idx in body["results"]["split"]["indices"]:
        assert isinstance(idx, int)


def test_index_exposes_dataset_mode():
    """The main page should expose the dataset-mode button and section."""
    r = client.get("/")
    assert r.status_code == 200
    assert 'id="mode-dataset-btn"' in r.text
    assert 'id="dataset-section"' in r.text
    assert 'otava-algo-checkbox' in r.text


def test_generate_with_otava_algorithm_orig():
    """The /api/generate endpoint should accept otava_algorithm=orig."""
    r = client.get(
        "/api/generate/step_function",
        params={
            "length": 100, "seed": 42,
            "run_otava": True, "otava_algorithm": "orig",
            "max_pvalue": 0.001,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "otava" in body
    # No error path expected here.
    assert "error" not in body["otava"]
    assert "parameters" in body["otava"], body["otava"]
    assert body["otava"]["parameters"]["algorithm"] == "orig"


def test_generate_rejects_unknown_otava_algorithm():
    r = client.get(
        "/api/generate/step_function",
        params={"length": 50, "seed": 42, "otava_algorithm": "nonexistent"},
    )
    assert r.status_code == 422


def test_analyze_accepts_otava_algorithm():
    """`/api/analyze` documents the otava_algorithm param — verify it actually works."""
    r = client.get(
        "/api/analyze/step_function",
        params={
            "length": 100, "seed": 42,
            "otava_algorithm": "orig",
            "max_pvalue": 0.001,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "otava" in body
    assert "error" not in body["otava"]
    assert body["otava"]["parameters"]["algorithm"] == "orig"


def test_compare_applies_per_algorithm_params():
    """`algorithm_params` should override the query-string defaults per algorithm,
    and missing per-algorithm keys should fall back to those defaults."""
    series = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    r = client.post(
        "/api/compare?max_pvalue=0.5&window_len=40",
        json={
            "data": series,
            "algorithms": ["split", "orig"],
            "algorithm_params": {
                "split": {"window_len": 20, "max_pvalue": 0.001},
                "orig":  {"max_pvalue": 0.01},
            },
        },
    )
    assert r.status_code == 200
    body = r.json()
    # The endpoint echoes back the resolved per-algorithm params so the UI can
    # display "what was actually run."
    assert body["algorithm_params"]["split"] == {
        "window_len": 20, "max_pvalue": 0.001, "min_magnitude": 0.0,
    }
    # `orig` only overrode max_pvalue; window_len falls back to the query default.
    assert body["algorithm_params"]["orig"] == {
        "window_len": 40, "max_pvalue": 0.01, "min_magnitude": 0.0,
    }


def test_compare_without_per_algorithm_params_uses_query_defaults():
    """`algorithm_params` is optional — falling back to query defaults must still work."""
    series = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    r = client.post(
        "/api/compare?max_pvalue=0.05",
        json={"data": series, "algorithms": ["split"]},
    )
    assert r.status_code == 200
    assert r.json()["algorithm_params"]["split"]["max_pvalue"] == 0.05


def test_detect_accepts_otava_algorithm():
    """`/api/detect` (used by mix mode) should respect the chosen algorithm."""
    series = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    r = client.post(
        "/api/detect?otava_algorithm=orig&max_pvalue=0.05",
        json={"data": series},
    )
    assert r.status_code == 200
    assert r.json()["parameters"]["algorithm"] == "orig"


def test_compare_returns_per_detection_details():
    """`/api/compare` results must carry per-detection stats so the frontend can
    render the detected-change-points table without a second API call."""
    series = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
    r = client.post(
        "/api/compare",
        json={"data": series, "algorithms": ["split"]},
    )
    assert r.status_code == 200
    split = r.json()["results"]["split"]
    assert split["indices"] == [7]
    # New fields required by the per-algorithm detected table:
    assert "change_points" in split
    assert len(split["change_points"]) == 1
    cp = split["change_points"][0]
    assert cp["index"] == 7
    for k in ("mean_before", "mean_after", "pvalue"):
        assert k in cp, f"missing {k} in {cp}"
        assert isinstance(cp[k], float)
    # Value checks: the step series [1.0]*7 + [5.0]*7 has clear segment means.
    assert cp["mean_before"] == pytest.approx(1.0, abs=0.01)
    assert cp["mean_after"] == pytest.approx(5.0, abs=0.01)
    assert 0.0 <= cp["pvalue"] <= 1.0
