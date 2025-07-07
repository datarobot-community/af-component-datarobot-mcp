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

# NOTE: This is only to be updated in the base component repository.

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_datarobot_token():
    """Fixture to provide mock DataRobot API token.

    This fixture is automatically used in all unit tests to ensure
    DataRobot credentials validation passes.
    """
    with patch.dict("os.environ", {"DATAROBOT_API_TOKEN": "test-token"}):
        yield
