import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs

import anyio
import asyncclick
import httpx

from exceptions import (
    PostmanAuthenticationError,
    PostmanCollectionNotFound,
    PostmanResponseNotHaveKey,
    PostmanRetrieveCollectionError,
    PostmanToManyRequestsError,
)

POSTMAN_API_BASE_URL = "https://api.getpostman.com"


@asyncclick.command(
    help="Export Postman collections into JSON format to provided path."
)
@asyncclick.option(
    "--path",
    "-p",
    type=asyncclick.types.Path(file_okay=False, dir_okay=True, exists=False),
    required=True,
    help="Path to the directory, where exported collections should be located.",
)
@asyncclick.option(
    "--collection-names",
    "-n",
    required=True,
    multiple=True,
    help="Names of the collections to be exported, separated by comma.",
)
@asyncclick.option(
    "--api-key",
    "-k",
    required=False,
    type=asyncclick.STRING,
    help="Postman API key for authentication.",
)
async def export(
    path: str, collection_names: tuple[str, ...], api_key: str | None = None
) -> None:
    """Starting point for exporting collections."""
    _path = Path(path)
    _path.mkdir(parents=True, exist_ok=True)

    if api_key is not None:
        os.environ["POSTMAN_API_KEY"] = api_key

    try:
        uids = await get_collections_uids_by_names(collection_names)
        await export_collections_to_json(uids, _path)
    except PostmanAuthenticationError as e:
        asyncclick.secho(str(e), fg="red", err=True)
        sys.exit(1)


async def export_collections_to_json(uids: Iterable[str], export_path: Path) -> None:
    """
    Exports Postman collections to JSON files.

    This function fetches collections from the Postman API using the provided collection
    IDs (uids), checks the response for any errors, and then saves each collection's
    data into a JSON file at the specified export path. The filename is based on the
    collection name and the current date.

    Args:
        uids (Iterable[str]): A list or iterable of Postman collection IDs to be exported.
        export_path (Path): The directory where the exported JSON files will be saved.

    Raises:
        PostmanAuthenticationError: If the API returns a 401 status code (authentication error).
        PostmanToManyRequestsError: If the API returns a 429 status code (too many requests).
        PostmanRetrieveCollectionError: If the API returns an unexpected status code.
        PostmanResponseNotHaveKey: If the expected data key is missing in the response.
        EnvironmentError: If POSTMAN_API_KEY neither exported into environment nor provided via --api-key parameter.


    Returns:
        None: This function performs an I/O operation (saving files) and does not return a value.
    """
    if not (postman_api_key := os.environ.get("POSTMAN_API_KEY", "")):
        raise EnvironmentError(
            "POSTMAN_API_KEY must be provided either in ENVIRONMENT (export POSTMAN_API_KEY=<key>) "
            "or passed in api-key parameter (--api-key <key>)"
        )
    async with httpx.AsyncClient(base_url=POSTMAN_API_BASE_URL) as client:
        tasks = [
            client.get(
                f"/collections/{uid}",
                headers={"X-API-Key": postman_api_key},
            )
            for uid in uids
        ]

        responses: list[httpx.Response] = await asyncio.gather(*tasks)

    for response in responses:
        data = response.json()
        if not response.is_success:
            match response.status_code:
                case 401:
                    raise PostmanAuthenticationError(data["error"]["message"])
                case 429:
                    raise PostmanToManyRequestsError
                case _:
                    raise PostmanRetrieveCollectionError(response.status_code)

        try:
            collection_name = (
                f"{data['collection']['info']['name']}_{datetime.now().date()}.json"
            )
        except KeyError as e:
            raise PostmanResponseNotHaveKey(e.args[0]) from e

        with open(export_path / collection_name, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=4)


async def get_collections_uids_by_names(names: Iterable[str]) -> list[str]:
    """
    Retrieve the UIDs of Postman collections by their names.

    Args:
        names (Iterable[str]): An iterable of collection names to search for.

    Returns:
        list[str]: A list of UIDs corresponding to the found collections.

    Raises:
        PostmanAuthenticationError: If authentication with the Postman API fails (HTTP 401).
        PostmanToManyRequestsError: If too many requests are sent to the Postman API (HTTP 429).
        PostmanRetrieveCollectionError: For any other HTTP error during collection retrieval.
        PostmanResponseNotHaveKey: If the expected keys are missing in the API response.
        PostmanCollectionNotFound: If no collection is found for a provided name.
        EnvironmentError: If POSTMAN_API_KEY neither exported into environment nor provided via --api-key parameter.
    """
    if not (postman_api_key := os.environ.get("POSTMAN_API_KEY", "")):
        raise EnvironmentError(
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
            )
            for name in names
        ]

        responses: list[httpx.Response] = await asyncio.gather(*tasks)

    for response in responses:
        data = response.json()
        if not response.is_success:
            match response.status_code:
                case 401:
                    raise PostmanAuthenticationError(data["error"]["message"])
                case 429:
                    raise PostmanToManyRequestsError
                case _:
                    raise PostmanRetrieveCollectionError(response.status_code)

        name = ""
        try:
            query_params: dict[str, list[str]] = parse_qs(
                response.request.url.query.decode(encoding="utf-8")
            )
            name: str = query_params.get("name", [""])[0]
            collections_uids.append(data["collections"][0]["uid"])
        except KeyError as e:
            raise PostmanResponseNotHaveKey(e.args[0]) from e
        except IndexError as e:
            raise PostmanCollectionNotFound(name) from e

    return collections_uids


if __name__ == "__main__":
    anyio.run(export.main)
