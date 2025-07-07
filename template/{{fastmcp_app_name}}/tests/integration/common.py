# Copyright 2025 DataRobot, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import MagicMock


class MockModel:
    """Mock DataRobot model object."""

    def __init__(self, model_id: str, model_type: str, metrics: dict):
        self.id = model_id
        self.model_type = model_type
        self.metrics = metrics

    def score(self, dataset_url: str):
        """Mock scoring method."""
        return MagicMock(id=f"job_{self.id}_{hash(dataset_url) % 1000}")


class MockProject:
    """Mock DataRobot project object."""

    def __init__(self, project_id: str, models=None):
        self.id = project_id
        self._models = models or []

    def get_models(self):
        """Mock get_models method."""
        return self._models


class MockDRClient:
    """Mock DataRobot client."""

    def __init__(self):
        self.Project = MagicMock()
        self.Model = MagicMock()
