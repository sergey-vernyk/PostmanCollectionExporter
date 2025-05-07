from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest

from src.postman_collection_exporter import exceptions
from src.postman_collection_exporter.exporters import JsonType
from src.postman_collection_exporter.helpers import (
    get_collections_content,
    get_collections_uids_by_names,
)

from . import mocks

# pylint: disable=missing-function-docstring


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names, expected_uids", [(("name1", "name2", "name3"), ("uid1", "uid2", "uid3"))]
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
    with pytest.raises(exceptions.EnvironmentVariableMissingError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert (
        str(exc_info.value) == "POSTMAN_API_KEY must be provided either in ENVIRONMENT "
        "(export POSTMAN_API_KEY=<key>) or passed in api-key parameter (--api-key <key>)"
    )


@pytest.mark.asyncio
async def test_get_uid_by_name_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_unauthenticated)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(exceptions.PostmanAuthenticationError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert (
        str(exc_info.value)
        == "Invalid API Key. Every request requires a valid API Key to be sent."
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_uid_by_name_too_many_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_many_requests)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(exceptions.PostmanTooManyRequestsError) as exc_info:
        await get_collections_uids_by_names(("name1", "name2"))

    assert str(exc_info.value) == "To many requests to API. Try again later."
    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, expected_status", [(400, 400), (500, 500), (404, 404)]
)
async def test_get_uid_by_name_collection_retrieval_error(
    status: int,
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_collection_retrieval_error(status))
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
async def test_get_uid_by_name_no_key_found_in_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_key_not_found_in_response)
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
    "names, expected_names",
    [(("name1", "name2", "name3"), ("name1", "name2", "name3"))],
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


@pytest.mark.asyncio
async def test_get_collection_content_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_collections_content)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    today = datetime.now()
    name_to_content: dict[str, JsonType] = {}

    collection_uids = ("collection_uid_1", "collection_uid_2")
    async for data, collection_name in get_collections_content(collection_uids):
        name_to_content[collection_name] = data

    sorted_by_name = dict(sorted(name_to_content.items(), key=lambda x: x[0]))

    assert all(today.strftime("%Y-%m-%d") in name for name in sorted_by_name.keys())

    assert all(
        data["collection"]["info"]["uid"] in collection_uids  # type: ignore
        for data in sorted_by_name.values()
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_collection_content_api_key_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_collections_content)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(exceptions.EnvironmentVariableMissingError) as exc_info:
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)
    assert (
        str(exc_info.value) == "POSTMAN_API_KEY must be provided either in ENVIRONMENT "
        "(export POSTMAN_API_KEY=<key>) or passed in api-key parameter (--api-key <key>)"
    )


@pytest.mark.asyncio
async def test_get_collections_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_unauthenticated)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(exceptions.PostmanAuthenticationError) as exc_info:
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert (
        str(exc_info.value)
        == "Invalid API Key. Every request requires a valid API Key to be sent."
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_collections_too_many_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_many_requests)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(exceptions.PostmanTooManyRequestsError) as exc_info:
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert str(exc_info.value) == "To many requests to API. Try again later."
    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, expected_status", [(400, 400), (500, 500), (404, 404)]
)
async def test_get_collections_retrieval_error(
    status: int,
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_collection_retrieval_error(status))
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(exceptions.PostmanCollectionRetrievalError) as exc_info:
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert (
        str(exc_info.value)
        == f"Error occurred while getting collection. Status: {expected_status}."
    )
    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_collections_no_key_found_in_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_key_not_found_in_response)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(exceptions.PostmanResponseMissingKeyError) as exc_info:
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)
    assert (
        str(exc_info.value)
        == "Response with collection does not have key 'collection'."
    )
    assert mock.call_count == 2
