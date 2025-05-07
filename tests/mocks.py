from typing import Any, Callable, Coroutine

import httpx

# pylint: disable=missing-function-docstring


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


async def mock_get_uids_by_name_unauthenticated(
    url: str,
    *,
    params: dict[str, Any],
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
        json={"error": {"message": "Unauthenticated."}},
        request=request,
    )


async def mock_get_uids_by_name_many_requests(
    url: str,
    *,
    params: dict[str, Any],
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


def mock_get_uids_by_name_collection_retrieval_error(
    status_code: int,
) -> Callable[..., Coroutine[Any, Any, httpx.Response]]:
    async def mock(
        url: str,
        *,
        params: dict[str, Any],
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


async def mock_get_uids_by_name_no_collections_key_found(
    url: str,
    *,
    params: dict[str, Any],
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
