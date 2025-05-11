"""
CLI Module for Postman Collection Exporter.

This module provides a command-line interface (CLI) for interacting with Postman collections.
It includes commands for exporting collections, archiving them, and scheduling actions using crontab.
"""

import getpass
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

import anyio
import asyncclick as click

from . import enums, exceptions, exporters, helpers, structures
from .cli_utils import CRONTAB_PATTERN, compose_cron_command


@click.group(help="CLI entry point providing commands for Postman collections.")
def cli() -> None:
    """CLI entry point for interacting with Postman collections."""


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
    required=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=False),
    help="Path to directory with collections being archived.",
)
@click.option(
    "--path-to-archive",
    "-a",
    required=True,
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


# pyright: reportArgumentType=false, reportOptionalMemberAccess=false
@click.command(help="Set crontab schedule for an action for Postman collections.")
@click.option(
    "--action",
    "-a",
    type=click.Choice(["export", "archive"], case_sensitive=False),
    required=True,
    help="Choose the Postman action to schedule.",
)
@click.option(
    "--pattern",
    "-p",
    type=CRONTAB_PATTERN,
    required=True,
    help='Crontab pattern (e.g., "0 0 * * *" for daily at midnight). Must be written within quotes!',
)
@click.option(
    "--comment",
    "-c",
    type=click.STRING,
    required=True,
    help="Comment added to the crontab entry (displayed next to the pattern).",
)
@click.option(
    "--user",
    "-u",
    type=click.STRING,
    required=False,
    default=lambda: getpass.getuser(),  # pylint: disable=unnecessary-lambda
    show_default=True,
    help="Username for the target crontab (default: current user).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show the crontab entry that would be created, without applying it.",
)
def set_schedule(
    action: Literal["export", "archive"],
    pattern: str,
    comment: str,
    user: str | bool,
    dry_run: bool = False,
) -> None:
    """
    Set a crontab schedule for a specified Postman action.

    Prompts the user for parameters required by the chosen action command
    and constructs a crontab entry to execute it periodically based on the given schedule.

    Args:
        action (Literal["export", "archive"]): The action to schedule.
        pattern (str): A valid crontab pattern (e.g., "* * * * *").
        comment (str): A comment to identify the schedule in crontab.
        user (str | bool): The user whose crontab will be modified.
        dry_run (bool, optional): If True, shows the generated crontab entry
            without actually applying it.

    Raises:
        OSError: If an OS-level error occurs during crontab setup.
        ValueError: If invalid data is provided.
        CronScheduleExistsError: If a duplicate crontab entry already exists.
    """

    action_to_command: dict[str, click.Command] = {"export": export, "archive": archive}

    if not click.confirm(
        f"Please, fill out params to schedule for the <{action}> command. Continue?"
    ):
        click.secho("Operation cancelled.", fg="yellow")
        return

    selected_command: click.Command = action_to_command[action]
    params: list[str] = []

    for param in selected_command.params:
        param_name = param.name.replace("_", "-")
        if param.multiple:
            while True:
                value: str = (
                    click.prompt(f"==> {param_name} (required)")
                    if param.required
                    else click.prompt(f"==> {param_name}", default=param.default or "")
                )
                if value.strip():
                    params.append(f"--{param_name}={value}")
                if not click.confirm(f"Any other value for '{param_name}'?"):
                    break
        else:
            value: str = (
                click.prompt(f"==> {param_name} (required)")
                if param.required
                else click.prompt(f"==> {param_name}", default=param.default or "")
            )
            if value.strip():
                params.append(f"--{param_name}={value}")

    cron_command = compose_cron_command(selected_command.name, params)
    cron_data = structures.CrontabData(
        command=cron_command, comment=comment, user=user, pattern=pattern
    )
    try:
        if not dry_run:
            result = helpers.set_cron_schedule(cron_data)
        else:
            click.secho(
                "\nThis is dry run operation. No actual changes have been made!",
                fg="yellow",
            )
            result = (
                f"\nCommand  ==> {cron_data.command}\n"
                f"Schedule ==> {cron_data.pattern}\n"
                f"Comment  ==> {cron_data.comment}\n"
                f"User     ==> {cron_data.user}\n"
            )
    except (OSError, ValueError, exceptions.CronScheduleExistsError) as e:
        click.secho(str(e), fg="red", err=True)
        sys.exit(1)
    else:
        click.secho(result, fg="green")


cli.add_command(export)
cli.add_command(archive)
cli.add_command(set_schedule)

if __name__ == "__main__":
    anyio.run(cli.main)
