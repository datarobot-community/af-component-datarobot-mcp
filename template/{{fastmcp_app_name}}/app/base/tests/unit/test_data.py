from unittest.mock import MagicMock, patch

import pytest

from app.base.tools import data


@pytest.mark.asyncio
async def test_upload_dataset_to_ai_catalog_success():
    with patch("app.base.tools.data.get_sdk_client") as mock_get_client, patch(
        "os.path.exists", return_value=True
    ):
        mock_client = MagicMock()
        mock_catalog_item = MagicMock()
        mock_catalog_item.id = "12345"
        mock_client.Dataset.create_from_file.return_value = mock_catalog_item
        mock_get_client.return_value = mock_client

        result = await data.upload_dataset_to_ai_catalog("somefile.csv")
        mock_client.Dataset.create_from_file.assert_called_once_with("somefile.csv")
        assert "AI Catalog ID: 12345" in result


@pytest.mark.asyncio
async def test_upload_dataset_to_ai_catalog_file_not_found():
    with patch("app.base.tools.data.get_sdk_client"), patch(
        "os.path.exists", return_value=False
    ):
        result = await data.upload_dataset_to_ai_catalog("nofile.csv")
        assert "File not found: nofile.csv" in result


@pytest.mark.asyncio
async def test_upload_dataset_to_ai_catalog_error():
    with patch("app.base.tools.data.get_sdk_client", side_effect=Exception("fail")):
        with pytest.raises(Exception) as exc_info:
            await data.upload_dataset_to_ai_catalog("somefile.csv")
        assert "Error in upload_dataset_to_ai_catalog: Exception: fail" == str(
            exc_info.value
        )


@pytest.mark.asyncio
async def test_list_ai_catalog_items_success():
    with patch("app.base.tools.data.get_sdk_client") as mock_get_client:
        mock_client = MagicMock()
        mock_ds1 = MagicMock()
        mock_ds1.id = "1"
        mock_ds1.name = "ds1"
        mock_ds2 = MagicMock()
        mock_ds2.id = "2"
        mock_ds2.name = "ds2"
        mock_client.Dataset.list.return_value = [mock_ds1, mock_ds2]
        mock_get_client.return_value = mock_client
        result = await data.list_ai_catalog_items()
        assert "1: ds1" in result
        assert "2: ds2" in result


@pytest.mark.asyncio
async def test_list_ai_catalog_items_empty():
    with patch("app.base.tools.data.get_sdk_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.Dataset.list.return_value = []
        mock_get_client.return_value = mock_client
        result = await data.list_ai_catalog_items()
        assert "No AI Catalog items found." in result


@pytest.mark.asyncio
async def test_list_ai_catalog_items_error():
    with patch("app.base.tools.data.get_sdk_client", side_effect=Exception("fail")):
        with pytest.raises(Exception) as exc_info:
            await data.list_ai_catalog_items()
        assert "Error in list_ai_catalog_items: Exception: fail" == str(exc_info.value)
