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

from tests.integration.common import MockDRClient, MockModel, MockProject


def create_test_mock_dr_client():
    """
    Create a mock DataRobot client with test project and models.
    """
    client = MockDRClient()

    # Create test project with mock models
    project = MockProject(
        "test_project_123",
        models=[
            MockModel("model_1", "XGBoost", {"AUC": 0.95, "LogLoss": 0.12}),
            MockModel("model_2", "Random Forest", {"AUC": 0.92, "LogLoss": 0.15}),
            MockModel("model_3", "LightGBM", {"AUC": 0.94, "LogLoss": 0.13}),
        ],
    )

    # Create standalone model
    standalone_model = MockModel("standalone_model", "Neural Network", {"AUC": 0.88})

    def mock_project_get(project_id):
        """Mock Project.get that returns appropriate project or raises exception."""
        if project_id == "test_project_123":
            return project
        elif project_id == "nonexistent_project":
            return None
        elif project_id == "test_project":
            raise Exception("DataRobot API error")
        else:
            return None

    def mock_model_get(project, model_id):
        """Mock Model.get that returns appropriate model."""
        if project.id == "test_project_123" and model_id == "standalone_model":
            return standalone_model
        else:
            return None

    # Configure the mock methods
    client.Project.get = mock_project_get
    client.Model.get = mock_model_get
    return client
