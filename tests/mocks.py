import builtins
import json
from pathlib import Path
from typing import Any, Callable, Coroutine

import aiofiles
import httpx

# pylint: disable=missing-function-docstring

fixtures_path = Path(__file__).parent / "fixtures"

real_import = builtins.__import__


async def mock_get_uids_by_names(
    url: str,
    *,
    params: dict[str, Any],
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    name_to_uid = {
        "name1": "uid1",
        "name2": "uid2",
        "name3": "uid3",
    }

    name = params["name"]
    uid = name_to_uid.get(name)

    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )
    return httpx.Response(
        status_code=200,
        json={"collections": [{"uid": uid}]},
        request=request,
    )


async def mock_postman_unauthenticated(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )
    return httpx.Response(
        status_code=401,
        json={
            "error": {
                "message": "Invalid API Key. Every request requires a valid API Key to be sent."
            }
        },
        request=request,
    )


async def mock_postman_many_requests(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )
    return httpx.Response(
        status_code=429,
        json={"detail": "To many requests to API. Try again later."},
        request=request,
    )


def mock_postman_collection_retrieval_error(
    status_code: int,
) -> Callable[..., Coroutine[Any, Any, httpx.Response]]:
    async def mock(
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        request = httpx.Request(
            method="GET",
            url=url,
            params=params,
            headers=headers or {},
        )
        return httpx.Response(
            status_code=status_code,
            json={
                "detail": f"Error occurred while getting collection. Status: {status_code}."
            },
            request=request,
        )

    return mock


async def mock_postman_key_not_found_in_response(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )
    return httpx.Response(
        status_code=200,
        json={},
        request=request,
    )


async def mock_get_uids_by_names_not_found(
    url: str,
    *,
    params: dict[str, Any],
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    name_to_coll_data = {
        "name1": {"collections": [{"uid": "collection1_uid"}]},
        "name2": {"collections": [{"uid": "collection2_uid"}]},
        "name3": {"collections": []},
    }

    name = params["name"]
    response_data = name_to_coll_data.get(name)

    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )
    return httpx.Response(
        status_code=200,
        json=response_data,
        request=request,
    )


async def mock_get_collections_content(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    **kwargs: Any,
) -> httpx.Response:
    uid = url.split("/")[-1]
    uid_to_filename = {
        "collection_uid_1": "test_data_collection_1.json",
        "collection_uid_2": "test_data_collection_2.json",
    }
    request = httpx.Request(
        method="GET",
        url=url,
        params=params,
        headers=headers or {},
    )

    filename = uid_to_filename.get(uid)

    if filename is None:
        raise ValueError(f"Unknown UID: {uid}.")

    async with aiofiles.open(f"{fixtures_path}/{filename}", encoding="utf-8") as fp:
        json_content = json.loads(await fp.read())

    return httpx.Response(status_code=200, json=json_content, request=request)


def mock_module_import(name: str, *args: Any, **kwargs: Any) -> None:
    if name == "crontab":
        raise ImportError(f"No module named '{name}'")

    return real_import(name, *args, **kwargs)
