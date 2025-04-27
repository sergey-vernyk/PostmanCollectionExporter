import asyncio
import os
from datetime import datetime
from http import HTTPStatus
from typing import AsyncGenerator, Iterable
from urllib.parse import parse_qs

import httpx

import exceptions
import exporters

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
        raise exceptions.EnvironmentVariablesMissingError(
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
        raise exceptions.EnvironmentVariablesMissingError(
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
