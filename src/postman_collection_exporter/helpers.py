"""
Helper functions for Postman Collection Exporter.

This module provides utility functions for interacting with the Postman API,
managing crontab schedules, and archiving exported collections.
"""

import asyncio
import os
import shutil
from collections.abc import AsyncGenerator, Iterable
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs

import httpx

from . import enums, exceptions, exporters

POSTMAN_API_BASE_URL = "https://api.getpostman.com"


async def get_collections_content(
    uids: Iterable[str],
) -> AsyncGenerator[tuple[exporters.JsonType, str], None]:
    """
    Fetch content of Postman collections by their UIDs.

    For each UID, retrieves collection data from the Postman API and yields it
    along with the filename to be used for export.

    Args:
        uids (Iterable[str]): UIDs of the collections to fetch.

    Yields:
        tuple[JsonType, str]: A tuple containing the collection data and the target filename.

    Raises:
        EnvironmentError: If the POSTMAN_API_KEY is missing.
        PostmanAuthenticationError: If authentication with the API fails (401 Unauthorized).
        PostmanToManyRequestsError: If the API rate limit is exceeded (429 Too Many Requests).
        PostmanRetrieveCollectionError: For other unexpected API errors.
        PostmanResponseNotHaveKey: If required keys are missing in the API response.
    """
    if not (postman_api_key := os.environ.get("POSTMAN_API_KEY", "")):
        raise exceptions.EnvironmentVariableMissingError(
            "POSTMAN_API_KEY must be provided either in ENVIRONMENT (export POSTMAN_API_KEY=<key>) "
            "or passed in api-key parameter (--api-key <key>)"
        )
    async with httpx.AsyncClient(base_url=POSTMAN_API_BASE_URL) as client:
        tasks = [
            client.get(
                f"/collections/{uid}",
                headers={"X-API-Key": postman_api_key},
                timeout=10,
            )
            for uid in uids
        ]

        today = datetime.now().date()

        for coro in asyncio.as_completed(tasks):
            response = await coro
            data = response.json()
            if not response.is_success:
                match response.status_code:
                    case HTTPStatus.UNAUTHORIZED.value:
                        raise exceptions.PostmanAuthenticationError(
                            data["error"]["message"]
                        )
                    case HTTPStatus.TOO_MANY_REQUESTS.value:
                        raise exceptions.PostmanTooManyRequestsError
                    case _:
                        raise exceptions.PostmanCollectionRetrievalError(
                            response.status_code
                        )

            try:
                collection_name = f"{data['collection']['info']['name']}_{today}.json"
            except KeyError as e:
                raise exceptions.PostmanResponseMissingKeyError(e.args[0]) from e

            yield data, collection_name


async def get_collections_uids_by_names(names: Iterable[str]) -> list[str]:
    """
    Retrieve UIDs of Postman collections by their names.

    Searches for collections by name and returns their UIDs.

    Args:
        names (Iterable[str]): Names of the collections to search.

    Returns:
        list[str]: List of collection UIDs matching the provided names.

    Raises:
        EnvironmentError: If the POSTMAN_API_KEY is missing.
        PostmanAuthenticationError: If authentication with the API fails (401 Unauthorized).
        PostmanToManyRequestsError: If the API rate limit is exceeded (429 Too Many Requests).
        PostmanRetrieveCollectionError: For other unexpected API errors.
        PostmanResponseNotHaveKey: If required keys are missing in the API response.
        PostmanCollectionNotFound: If a collection with the specified name is not found.
    """
    if not (postman_api_key := os.environ.get("POSTMAN_API_KEY", "")):
        raise exceptions.EnvironmentVariableMissingError(
            "POSTMAN_API_KEY must be provided either in ENVIRONMENT (export POSTMAN_API_KEY=<key>) "
            "or passed in api-key parameter (--api-key <key>)"
        )

    collections_uids: list[str] = []

    async with httpx.AsyncClient(base_url=POSTMAN_API_BASE_URL) as client:
        tasks = [
            client.get(
                "/collections/",
                headers={"X-API-Key": postman_api_key},
                params={"name": name},
                timeout=10,
            )
            for name in names
        ]

        for coro in asyncio.as_completed(tasks):
            response = await coro
            data = response.json()
            if not response.is_success:
                match response.status_code:
                    case HTTPStatus.UNAUTHORIZED.value:
                        raise exceptions.PostmanAuthenticationError(
                            data["error"]["message"]
                        )
                    case HTTPStatus.TOO_MANY_REQUESTS.value:
                        raise exceptions.PostmanTooManyRequestsError
                    case _:
                        raise exceptions.PostmanCollectionRetrievalError(
                            response.status_code
                        )

            name = ""
            try:
                query_params: dict[str, list[str]] = parse_qs(
                    response.request.url.query.decode(encoding="utf-8")
                )
                name: str = query_params.get("name", [""])[0]
                collections_uids.append(data["collections"][0]["uid"])
            except KeyError as e:
                raise exceptions.PostmanResponseMissingKeyError(e.args[0]) from e
            except IndexError as e:
                raise exceptions.PostmanCollectionNotFoundError(name) from e

    return collections_uids


def archive_collections(
    collections_path: Path,
    archive_name: str,
    archive_type: enums.ArchiveType = enums.ArchiveType.ZIP,
) -> str:
    """
    Create an archive from a directory containing Postman collections.

    Args:
        collections_path (Path): Path to the directory containing collection files.
        archive_type (enums.ArchiveType): Type of archive to create (e.g., 'zip', 'tar'). Default: zip.
        archive_name (str): Full path and base name of the archive to be created (excluding extension).

    Raises:
        FileNotFoundError: If the collections directory is empty.
        ArchiveCreateError: If an error occurs during archive creation.

    Returns:
        str: Full path to the created archive.
            E.g `/home/user/Archives/Postman_archived_collections.zip`
    """
    if not any(Path(collections_path).iterdir()):
        raise FileNotFoundError(
            f"No collection files found in directory '{collections_path}'."
        )

    try:
        return shutil.make_archive(
            archive_name, archive_type, root_dir=collections_path
        )
    except (ValueError, NotADirectoryError) as e:
        raise exceptions.ArchiveCreateError(f"Failed to create archive: {e}.") from e
