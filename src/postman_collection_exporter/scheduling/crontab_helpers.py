from collections.abc import Generator
from typing import TYPE_CHECKING

from .. import exceptions, structures
from ..dependencies.utils import ensure_crontab_is_installed

if TYPE_CHECKING:
    import crontab


def set_cron_schedule(cron_data: structures.CrontabData) -> str:
    """
    Configures crontab schedule on Unix-based systems.

    Args:
        cron_data (CrontabData): An object containing the following attributes:
            - `pattern` (str): The cron pattern specifying the schedule.
            - `command` (str): The command to execute.
            - `comment` (str): A comment to identify the cron job.
            - `user` (str | bool): The user for whom the cron job is created.
            - `filename` (Optional[Path]): Path to the file where the cron job
              should be written. If not provided, the job is written to the
              user's crontab.

    Returns:
        str: A formatted string summarizing the created cron job, including:
            - Command
            - Schedule
            - Comment
            - User

    Raises:
        OSError: If the system is Windows, as cron scheduling is not supported.
        RuntimeError: If the `python-crontab` library is not installed.
        ValueError: If the provided cron pattern is invalid.
        CronScheduleExistsError: If a cron job with the same schedule, comment,
            and command already exists.
    """
    # pylint: disable=import-outside-toplevel

    ensure_crontab_is_installed()

    import platform

    import crontab

    if platform.system() == "Windows":
        raise OSError(
            "Cron scheduling isn't available on Windows. Consider using Task Scheduler."
        )

    if not crontab.CronSlices.is_valid(cron_data.pattern):
        raise ValueError(f"Cron pattern [{cron_data.pattern}] isn't valid.")

    cron = crontab.CronTab(user=cron_data.user)

    for job in cron.find_command(cron_data.command):
        raise exceptions.CronScheduleExistsError(
            cron_data.pattern, job.comment, job.command or "No command."
        )
    job = cron.new(
        cron_data.command,
        cron_data.comment,
        user=cron_data.user if isinstance(cron_data.user, str) else None,
    )
    job.setall(cron_data.pattern)
    job.enable()

    if cron_data.filename is not None:
        cron_data.filename.touch()
        cron.write(str(cron_data.filename), user=cron_data.user, errors=True)
    else:
        cron.write_to_user()

    return (
        f"\nCommand  ==> {cron_data.command}\n"
        f"Schedule ==> {cron_data.pattern}\n"
        f"Comment  ==> {cron_data.comment}\n"
        f"User     ==> {cron_data.user}\n"
    )


def get_cron_schedules(
    pattern: str | None = None, user: str | None = None, show_all: bool = False
) -> Generator["crontab.CronItem", None, None]:
    """
    Retrieve cron schedule entries based on a pattern, user, or all available jobs.

    Args:
        pattern (str | None, optional): A cron pattern string to filter jobs by schedule. Defaults to None.
        user (str | None, optional): The username to filter jobs by owner. Defaults to None.
        show_all (bool, optional): If True, yields all available cron jobs regardless of pattern or user.
            Defaults to False.

    Yields:
        crontab.CronItem: Cron job entries matching the specified criteria.

    Raises:
        OSError: If the function is called on a Windows system where cron is not available.
        ValueError: If a provided cron pattern is invalid.

    Note:
        - Requires the 'crontab' and 'crontabs' Python packages.
        - Only one of 'pattern', 'user', or 'show_all' should be used at a time for meaningful results.
    """
    # pylint: disable=import-outside-toplevel

    ensure_crontab_is_installed()

    import platform

    import crontab
    import crontabs

    if platform.system() == "Windows":
        raise OSError(
            "Cron scheduling isn't available on Windows. Consider using Task Scheduler."
        )

    if show_all:
        yield from crontabs.CronTabs().all

    elif pattern is not None:
        if not crontab.CronSlices.is_valid(pattern):
            raise ValueError(f"Cron pattern [{pattern}] isn't valid.")

        yield from crontabs.CronTabs().all.find_time(pattern)

    elif user is not None:
        for job in crontabs.CronTabs().all:
            if user == job.user:
                yield job
