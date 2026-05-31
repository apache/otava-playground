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

"""Tests for the bundled real-world datasets."""


from otava_test_data.datasets import DATASETS, get_dataset, list_datasets


def test_list_includes_tigerbeetle():
    names = [d["name"] for d in list_datasets()]
    assert "tigerbeetle" in names


def test_get_unknown_returns_none():
    assert get_dataset("not-a-dataset") is None


def test_tigerbeetle_metadata_and_shape():
    ds = get_dataset("tigerbeetle")
    assert ds is not None
    assert ds["name"] == "tigerbeetle"
    assert ds["title"]
    assert ds["description"]
    assert isinstance(ds["series"], list)
    # Same length as the upstream apache/otava perf_test.py series.
    assert len(ds["series"]) == 365
    assert all(isinstance(v, (int, float)) for v in ds["series"])


def test_list_omits_series_payload():
    # list_datasets() should not echo the full series — only metadata.
    for d in list_datasets():
        assert "series" not in d


def test_registry_keyed_by_name():
    for name, ds in DATASETS.items():
        assert ds["name"] == name
