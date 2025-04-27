import os
import sys
from pathlib import Path

import anyio
import asyncclick as click

import exceptions
import exporters
import helpers


@click.command(
    help="Export Postman collections into JSON format to the specified path."
)
@click.option(
    "--path",
    "-p",
    type=click.types.Path(file_okay=False, dir_okay=True, exists=False),
    required=True,
    help="Directory, where exported collections will be located.",
)
@click.option(
    "--collection-names",
    "-n",
    required=True,
    multiple=True,
    help="Names of the Postman collections to be export.",
)
@click.option(
    "--api-key",
    "-k",
    required=False,
    type=click.STRING,
    help="Optional Postman API key for authentication. Overrides environment variable.",
)
async def export(
    path: str, collection_names: tuple[str, ...], api_key: str | None = None
) -> None:
    """
    Export selected Postman collections to JSON files.

    Prepares the export directory, optionally sets the API key, retrieves collection UIDs by names,
    and saves each collection to a JSON file.

    Args:
        path (str): Target directory for exported JSON files.
        collection_names (tuple[str, ...]): Names of collections to export.
        api_key (str | None, optional): Postman API key for authentication. Defaults to None.

    Raises:
        SystemExit: If any error with the Postman API occurred or no environment variable is found.
    """
    _path = Path(path)
    _path.mkdir(parents=True, exist_ok=True)

    if api_key is not None:
        os.environ["POSTMAN_API_KEY"] = api_key

    try:
        uids: list[str] = await helpers.get_collections_uids_by_names(collection_names)

        async for data, collection_name in helpers.get_collections_content(uids):
            await exporters.export_to_json(_path, collection_name, data)

    except (
        exceptions.PostmanAPIError,
        exceptions.EnvironmentVariablesMissingError,
    ) as e:
        click.secho(str(e), fg="red", err=True)
        sys.exit(1)

    click.secho(
        f"Collections ({', '.join(collection_names)}) have been exported successfully.",
        fg="green",
    )


if __name__ == "__main__":
    anyio.run(export.main)
