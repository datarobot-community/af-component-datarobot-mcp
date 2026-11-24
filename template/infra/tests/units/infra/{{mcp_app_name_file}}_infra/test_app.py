# Copyright 2026 DataRobot, Inc.
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

from pathlib import Path

import pytest

from . import APP_NAME, app_module

_app = app_module("_app")


def test_app_name_comes_from_the_package_directory() -> None:
    assert _app.APP_NAME == APP_NAME
    assert _app.INFRA_PACKAGE_DIR.name == f"{APP_NAME}_infra"


def test_legacy_user_params_file_stops_the_deploy(tmp_path: Path) -> None:
    (tmp_path / f"{APP_NAME}_user_params.py").write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match=f"{APP_NAME}_infra/user_params.py"):
        _app.assert_no_legacy_user_params(tmp_path)


def test_no_legacy_user_params_file_passes(tmp_path: Path) -> None:
    _app.assert_no_legacy_user_params(tmp_path)
