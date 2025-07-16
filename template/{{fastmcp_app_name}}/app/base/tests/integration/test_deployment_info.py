import pytest
from mcp.types import TextContent

from .mcp_utils import integration_test_mcp_session


@pytest.mark.asyncio
class TestMCPDeploymentInfoIntegration:
    """Integration tests for MCP deployment info tools (multiclass project)."""

    async def test_get_deployment_features_and_template(self, classification_project):
        """Integration test for get_deployment_features and generate_prediction_data_template on a multiclass deployment."""
        async with integration_test_mcp_session() as session:
            deployment_id = classification_project["deployment_id"]
            # Test get_deployment_features
            result = await session.call_tool(
                "get_deployment_features",
                {"deployment_id": deployment_id},
            )
            assert not result.isError, (
                f"get_deployment_features failed: {result.content[0].text}"
            )
            result_content = result.content[0]
            assert isinstance(result_content, TextContent)
            assert "error" not in result_content.text.lower()

            # Test generate_prediction_data_template
            result = await session.call_tool(
                "generate_prediction_data_template",
                {"deployment_id": deployment_id, "n_rows": 3},
            )
            assert not result.isError, (
                f"generate_prediction_data_template failed: {result.content[0].text}"
            )
            result_content = result.content[0]
            assert isinstance(result_content, TextContent)
            empty_lines = ",\n" * 3
            assert result_content.text == (
                f"# Prediction Data Template for Deployment: {deployment_id}\n"
                "# Model Type: Keras Text Convolutional Neural Network Classifier\n"
                "# Target: sentiment (Type: Multiclass)\n"
                "# Total Features: 2\n"
                "text_review,product_category\n"
                f"{empty_lines}"
            )
