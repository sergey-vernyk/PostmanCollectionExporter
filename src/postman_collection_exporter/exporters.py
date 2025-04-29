import json
from pathlib import Path
from typing import Mapping, TypeAlias

import aiofiles

JsonType: TypeAlias = (
    Mapping[str, "JsonType"] | list["JsonType"] | str | int | float | bool | None
)


async def export_to_json(
    export_path: Path, collection_name: str, data: JsonType
) -> None:
    """
    Save JSON data asynchronously to a file.

    Args:
        export_path (Path): Target directory for saving the JSON file.
        collection_name (str): Name of the JSON file (should include .json extension).
        data (JsonType): Data to serialize and save.
    """
    async with aiofiles.open(
        export_path / collection_name, "w", encoding="utf-8"
    ) as fp:
        await fp.write(json.dumps(data, indent=4))
