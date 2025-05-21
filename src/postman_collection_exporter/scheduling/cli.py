import getpass
import sys
from typing import Literal

import asyncclick as click

from postman_collection_exporter import exceptions, structures

from ..dependencies.utils import ensure_crontab_is_installed
from . import crontab_helpers
from .utils import CRONTAB_PATTERN, compose_cron_command


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
    ensure_crontab_is_installed()
    # pylint: disable=import-outside-toplevel
    from ..cli import archive, export

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
            result = crontab_helpers.set_cron_schedule(cron_data)
        else:
            click.secho(
                "\nThis is dry run operation. No actual changes have been made!\n",
                fg="yellow",
            )
            result = (
                f"Command  ==> {cron_data.command}\n"
                f"Schedule ==> {cron_data.pattern}\n"
                f"Comment  ==> {cron_data.comment}\n"
                f"User     ==> {cron_data.user}\n"
            )
    except (OSError, ValueError, exceptions.CronScheduleExistsError) as e:
        click.secho(str(e), fg="red", err=True)
        sys.exit(1)
    else:
        click.secho(result, fg="green")
