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

from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.base.core.constants import RUNTIME_PARAM_ENV_VAR_NAME_PREFIX


class RecipeAppConfig(BaseSettings):
    """Recipe-specific application configuration."""

    # Example of adding recipe-specific configuration
    recipe_name: str = Field(
        default="default-recipe",
        validation_alias=AliasChoices(
            RUNTIME_PARAM_ENV_VAR_NAME_PREFIX + "RECIPE_NAME",
            "RECIPE_NAME",
        ),
        description="Name of the recipe being used",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global configuration instance
_recipe_config: Optional[RecipeAppConfig] = None


def get_recipe_config() -> RecipeAppConfig:
    """Get the global recipe configuration instance."""
    global _recipe_config
    if _recipe_config is None:
        _recipe_config = RecipeAppConfig()
    return _recipe_config
