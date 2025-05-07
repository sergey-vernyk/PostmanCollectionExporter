import os
import sys
from datetime import datetime
from pathlib import Path

import anyio
import asyncclick as click

from . import enums, exceptions, exporters, helpers


@click.group(help="CLI entry point providing commands for Postman collections.")
def cli() -> None:
    """
    CLI entry point for interacting with Postman collections.
    """


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
        PostmanAPIError: If any error with the Postman API occurred or no environment variable is found.
        EnvironmentVariablesMissingError: If POSTMAN_API_KEY environment variable is not set.
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
        exceptions.EnvironmentVariableMissingError,
    ) as e:
        click.secho(str(e), fg="red", err=True)
        sys.exit(1)

    click.secho(
        f"Collections ({', '.join(collection_names)}) have been exported successfully.",
        fg="green",
    )


# TODO add properly handling collection names with spaces
@click.command(
    help="Archive a directory containing Postman collections into an archive file."
)
@click.option(
    "--path-to-collections",
    "-c",
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to directory with collections being archived.",
)
@click.option(
    "--path-to-archive",
    "-a",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help="Path to directory with an archive being created.",
)
@click.option(
    "--name",
    "-n",
    type=click.STRING,
    required=True,
    help="Name of the archive being created.",
)
@click.option(
    "--archive-type",
    required=False,
    default="zip",
    show_default=True,
    type=click.Choice(
        ("zip", "tar", "gztar", "bztar", "xztar"),
        case_sensitive=False,
    ),
    help="Type of archive being created.",
)
async def archive(
    path_to_collections: str,
    path_to_archive: str,
    name: str,
    archive_type: enums.ArchiveType = enums.ArchiveType.ZIP,
) -> None:
    """
    Archive a directory containing exported Postman collections.

    Args:
        path_to_collections (str): Path to the directory containing exported Postman collections.
        path_to_archive (str): Path to the directory where the archive will be saved.
        name (str): Base name of the resulting archive file (without extension).
        archive_type (enums.ArchiveType, optional): Format of the archive to create.
            Supported formats include 'zip', 'tar', 'gztar', 'bztar', and 'xztar'. Defaults to 'zip'.

    Raises:
        FileNotFoundError: If the specified directory with collections is empty or does not exist.
        ArchiveCreateError: If an error occurs during the archive creation process.
    """
    _collections_path = Path(path_to_collections)
    _archive_path = Path(path_to_archive)
    _archive_path.mkdir(exist_ok=True, parents=True)

    archive_name = _archive_path / f"{name}_{datetime.now().date()}"

    try:
        helpers.archive_collections(_collections_path, str(archive_name), archive_type)
    except (exceptions.ArchiveCreateError, FileNotFoundError) as e:
        click.secho(str(e), fg="red", err=True)
        sys.exit(1)

    click.secho(
        f"Archive '{archive_name.stem}.{archive_type}' has been created in '{_archive_path}' directory.",
        fg="green",
    )


cli.add_command(export)
cli.add_command(archive)

if __name__ == "__main__":
    anyio.run(cli.main)
