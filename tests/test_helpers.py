from unittest.mock import AsyncMock

import httpx
import pytest

from src.postman_collection_exporter import exceptions
from src.postman_collection_exporter.helpers import get_collections_uids_by_names

from . import mocks

# pylint: disable=missing-function-docstring


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names,expected_uids", [(("name1", "name2", "name3"), ("uid1", "uid2", "uid3"))]
)
async def test_get_uid_by_name_success(
    names: tuple[str, ...],
    expected_uids: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_names)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")
    uids = await get_collections_uids_by_names(names)
    # as_completed() function can return results in any order
    assert sorted(uids) == sorted(expected_uids)


@pytest.mark.asyncio
async def test_get_uid_by_name_apikey_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_names)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    with pytest.raises(exceptions.EnvironmentVariablesMissingError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert (
        str(exc_info.value) == "POSTMAN_API_KEY must be provided either in ENVIRONMENT "
        "(export POSTMAN_API_KEY=<key>) or passed in api-key parameter (--api-key <key>)"
    )


@pytest.mark.asyncio
async def test_get_uid_by_name_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_name_unauthenticated)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(exceptions.PostmanAuthenticationError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert str(exc_info.value) == "Unauthenticated."
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_uid_by_name_too_many_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_name_many_requests)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(exceptions.PostmanTooManyRequestsError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert str(exc_info.value) == "To many requests to API. Try again later."
    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status,expected_status", [(400, 400), (500, 500), (404, 404)])
async def test_get_uid_by_name_collection_retrieval_error(
    status: int,
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(
        side_effect=mocks.mock_get_uids_by_name_collection_retrieval_error(status)
    )
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(exceptions.PostmanCollectionRetrievalError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert (
        str(exc_info.value)
        == f"Error occurred while getting collection. Status: {expected_status}."
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_uid_by_name_no_collection_key_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_name_no_collections_key_found)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(exceptions.PostmanResponseMissingKeyError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert (
        str(exc_info.value)
        == "Response with collection does not have key 'collections'."
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names,expected_names", [(("name1", "name2", "name3"), ("name1", "name2", "name3"))]
)
async def test_get_uid_by_name_no_collections_found(
    names: tuple[str, ...],
    expected_names: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_names_not_found)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(exceptions.PostmanCollectionNotFoundError) as exc_info:
        await get_collections_uids_by_names(names)

    assert (
        str(exc_info.value)
        == f"Collection not found with provided name: '{expected_names[2]}'."
    )
    assert mock.call_count == 3
