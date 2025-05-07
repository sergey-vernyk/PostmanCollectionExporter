import os
import tarfile
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from src.postman_collection_exporter import enums, exceptions
from src.postman_collection_exporter.exporters import JsonType
from src.postman_collection_exporter.helpers import (
    archive_collections,
    get_collections_content,
    get_collections_uids_by_names,
)

from . import mocks

# pylint: disable=missing-function-docstring

# ----- Get Collections UIDs By Collections Names -----


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names, expected_uids", [(("name1", "name2", "name3"), ("uid1", "uid2", "uid3"))]
)
async def test_get_uids_by_names_success(
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
async def test_get_uids_by_names_apikey_not_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_names)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    with pytest.raises(
        exceptions.EnvironmentVariableMissingError,
        match="POSTMAN_API_KEY must be provided either in ENVIRONMENT "
        r"\(export POSTMAN_API_KEY=\<key\>\) or passed in api-key parameter \(--api-key \<key\>\)",
    ):
        await get_collections_uids_by_names(("name1", "name2"))


@pytest.mark.asyncio
async def test_get_uid_by_name_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_unauthenticated)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(
        exceptions.PostmanAuthenticationError,
        match="Invalid API Key. Every request requires a valid API Key to be sent.",
    ):
        await get_collections_uids_by_names(("name1", "name2"))

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_uids_by_names_too_many_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_many_requests)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    # simulate unauthenticated API response for both collection names
    with pytest.raises(
        exceptions.PostmanTooManyRequestsError,
        match="To many requests to API. Try again later.",
    ):
        await get_collections_uids_by_names(("name1", "name2"))

    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status, expected_status", [(400, 400), (500, 500), (404, 404)]
)
async def test_get_uids_by_names_collection_retrieval_error(
    status: int,
    expected_status: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_collection_retrieval_error(status))
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(
        exceptions.PostmanCollectionRetrievalError,
        match=f"Error occurred while getting collection. Status: {expected_status}.",
    ):
        await get_collections_uids_by_names(("name1", "name2"))

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_uids_by_names_no_key_found_in_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_key_not_found_in_response)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(
        exceptions.PostmanResponseMissingKeyError,
        match="Response with collection does not have key 'collections'.",
    ):
        await get_collections_uids_by_names(("name1", "name2"))

    assert mock.call_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "names, expected_names",
    [(("name1", "name2", "name3"), ("name1", "name2", "name3"))],
)
async def test_get_uids_by_names_no_collections_found(
    names: tuple[str, ...],
    expected_names: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_get_uids_by_names_not_found)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    with pytest.raises(
        exceptions.PostmanCollectionNotFoundError,
        match=f"Collection not found with provided name: '{expected_names[2]}'.",
    ):
        await get_collections_uids_by_names(names)

    assert mock.call_count == 3


# ----- Get Collections Content By Collections IDs -----


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
    with pytest.raises(
        exceptions.EnvironmentVariableMissingError,
        match="POSTMAN_API_KEY must be provided either in ENVIRONMENT "
        r"\(export POSTMAN_API_KEY=\<key\>\) or passed in api-key parameter \(--api-key \<key\>\)",
    ):
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)


@pytest.mark.asyncio
async def test_get_collections_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_unauthenticated)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(
        exceptions.PostmanAuthenticationError,
        match="Invalid API Key. Every request requires a valid API Key to be sent.",
    ):
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_collections_too_many_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_many_requests)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(
        exceptions.PostmanTooManyRequestsError,
        match="To many requests to API. Try again later.",
    ):
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

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
    with pytest.raises(
        exceptions.PostmanCollectionRetrievalError,
        match=f"Error occurred while getting collection. Status: {expected_status}.",
    ):
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert mock.call_count == 2


@pytest.mark.asyncio
async def test_get_collections_no_key_found_in_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock = AsyncMock(side_effect=mocks.mock_postman_key_not_found_in_response)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock)
    monkeypatch.setenv("POSTMAN_API_KEY", "test_api_key")

    collection_uids = ("collection_uid_1", "collection_uid_2")
    with pytest.raises(
        exceptions.PostmanResponseMissingKeyError,
        match="Response with collection does not have key 'collection'.",
    ):
        async for data, collection_name in get_collections_content(collection_uids):
            print(data, collection_name)

    assert mock.call_count == 2


# ----- Archive Collections -----


@pytest.mark.parametrize("archive_type", ("zip", "tar", "gztar", "bztar", "xztar"))
def test_archive_collections_success(archive_type: enums.ArchiveType) -> None:
    collections_path = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as archive_dir:
        archive_name = f"{archive_dir}/Postman_archived_collections"

        path_to_created_archive = archive_collections(
            collections_path, archive_name, archive_type
        )
        created_archive_name = path_to_created_archive.rsplit("/", maxsplit=1)[-1]

        assert len(os.listdir(archive_dir)) == 1, (
            "Directory for archives must have only one created archive."
        )
        assert os.listdir(archive_dir)[0] == created_archive_name, (
            "The file in the directory with archives must have the same name as the created archive."
        )
        assert os.path.getsize(path_to_created_archive) > 0, (
            "Created archive must not to be empty."
        )

        if archive_type == enums.ArchiveType.ZIP:
            with zipfile.ZipFile(path_to_created_archive) as file:
                assert sorted(file.namelist()) == sorted(os.listdir(collections_path))
        else:
            with tarfile.open(path_to_created_archive) as file:
                # need to remove './' characters because 'file.getnames()' uses relative paths in result list
                # e.g. [".", "./test_data_collection_1.json", "./test_data_collection_2.json"]
                assert sorted(name.strip("./") for name in file.getnames())[
                    1:
                ] == sorted(os.listdir(collections_path))


def test_archive_collections_invalid_archive_type() -> None:
    collections_path = Path(__file__).parent / "fixtures"
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as archive_dir:
        archive_name = f"{archive_dir}/Postman_archived_collections"

        with pytest.raises(
            exceptions.ArchiveCreateError,
            match="Failed to create archive: unknown archive format 'invalid_type'.",
        ):
            archive_collections(
                collections_path,
                archive_name,
                "invalid_type",  # type: ignore (must be that only for test)
            )


def test_archive_collections_defined_not_a_directory_with_collections() -> None:
    with tempfile.NamedTemporaryFile(
        dir=Path(__file__).parent
    ) as archive_file_but_must_be_dir:
        archive_name = (
            f"{archive_file_but_must_be_dir.name}/Postman_archived_collections"
        )

        with pytest.raises(NotADirectoryError, match="Not a directory:"):
            archive_collections(
                Path(archive_file_but_must_be_dir.name),
                archive_name,
                enums.ArchiveType.TAR,
            )


def test_archive_collections_empty_directory_for_collections() -> None:
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as coll_dir:
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as archive_dir:
            archive_name = f"{archive_dir}/Postman_archived_collections"

            with pytest.raises(
                FileNotFoundError, match="No collection files found in directory"
            ):
                archive_collections(
                    Path(coll_dir), archive_name, enums.ArchiveType.XZTAR
                )
