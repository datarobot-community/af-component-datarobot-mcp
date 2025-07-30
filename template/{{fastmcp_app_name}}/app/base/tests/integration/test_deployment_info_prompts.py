import pytest
from mcp.types import (
    GetPromptResult,
    ListPromptsResult,
    PromptMessage,
)

from .mcp_utils import integration_test_mcp_session


@pytest.mark.asyncio
class TestMCPDeploymentInfoPromptIntegration:
    """Integration tests for MCP deployment info prompt."""

    async def test_deployment_info_prompt(self, classification_project):
        """Complete integration test for MCP deployment info prompt"""

        async with integration_test_mcp_session() as session:
            # 1 Test listing available prompts
            prompts_result: ListPromptsResult = await session.list_prompts()
            prompt_names = [prompt.name for prompt in prompts_result.prompts]

            assert "get_deployment_info_prompt" in prompt_names

            # 2 Test getting deployment info
            deployment_id = classification_project["deployment_id"]
            result: GetPromptResult = await session.get_prompt(
                "get_deployment_info_prompt",
                {
                    "deployment_id": deployment_id,
                },
            )

            assert len(result.messages) > 0
            assert isinstance(result.messages[0], PromptMessage)

            result_text = result.messages[0].content.text
            result_role = result.messages[0].role
            assert result_role == "user", f"Result role: {result_role}"
            expected_text = f"""
    Show me detailed information about deployment {deployment_id}, including:
    - Model type and configuration
    - Required features and their importance
    - Target variable details
    - Time series configuration (if applicable)
    """
            assert result_text == expected_text, f"Result text: {result_text}"
