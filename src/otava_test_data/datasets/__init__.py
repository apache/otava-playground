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

"""Real-world performance datasets bundled for algorithm comparison."""

from otava_test_data.datasets.tigerbeetle import TIGERBEETLE

DATASETS = {
    TIGERBEETLE["name"]: TIGERBEETLE,
}


def list_datasets() -> list[dict]:
    """Return metadata for every bundled dataset (without the series itself)."""
    return [
        {"name": ds["name"], "title": ds["title"], "description": ds["description"]}
        for ds in DATASETS.values()
    ]


def get_dataset(name: str) -> dict | None:
    """Return the full dataset entry (series + metadata) or None if unknown."""
    return DATASETS.get(name)
