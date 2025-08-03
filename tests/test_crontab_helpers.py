import builtins
import getpass
import platform
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from src.postman_collection_exporter import exceptions, structures
from src.postman_collection_exporter.scheduling import crontab_helpers

from . import mocks

# pylint: disable=missing-function-docstring


def remove_cron_job_by_comment(comment: str) -> None:
    """Gets current crontab lines finds line which contain the `comment` and removes the line."""
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True, check=True
    )

    lines = [line for line in result.stdout.splitlines() if line.strip()]

    for index, line in enumerate(lines):
        if comment in line:
            lines.pop(index)
            subprocess.run(
                ["crontab", "-"],
                input="\n".join(lines) + "\n",
                text=True,
                check=True,
            )


# ----- Set Schedule Into User Crontab or Save It To File -----


@pytest.mark.asyncio
async def test_set_schedule_crontab_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(builtins, "__import__", mocks.mock_module_import)

    with pytest.raises(
        RuntimeError,
        match=(
            "The 'python-crontab' package is required for scheduling functionality. "
            "Install it using 'pip install python-crontab'."
        ),
    ):
        crontab_data = structures.CrontabData(
            command=(
                "/home/user/.venv/bin/python "
                "-m postman_collection_exporter.cli "
                "archive "
                "--path-to-collections=path_to_archive "
                "--path-to-archive=archive_name "
                "--name=archive_name "
                "--archive-type=zip "
                "--log-path=/home/user/crontab/cron.log"
            ),
            comment="Some comment",
            pattern="* * * * *",
            user=getpass.getuser(),
        )
        crontab_helpers.set_cron_schedule(crontab_data)


@pytest.mark.asyncio
async def test_set_schedule_run_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Windows")

    with pytest.raises(
        OSError,
        match="Cron scheduling isn't available on Windows. Consider using Task Scheduler.",
    ):
        crontab_data = structures.CrontabData(
            command=(
                "/home/user/.venv/bin/python "
                "-m postman_collection_exporter.cli "
                "archive "
                "--path-to-collections=path_to_archive "
                "--path-to-archive=archive_name "
                "--name=archive_name "
                "--archive-type=zip "
                "--log-path=/home/user/crontab/cron.log"
            ),
            comment="Some comment",
            pattern="* * * * *",
            user=getpass.getuser(),
        )
        crontab_helpers.set_cron_schedule(crontab_data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pattern",
    (
        "* * * *",
        "* * * * * *",
        "70 * * * *",
        "* 25 * * *",
        "* * 0 * *",
        "*/-5 * * * *",
        "*/* * * * *",
        "5-2 * * * *",
    ),
)
async def test_set_schedule_cron_pattern_invalid(pattern: str) -> None:
    with pytest.raises(
        ValueError,
        match=re.escape(f"Cron pattern [{pattern}] isn't valid."),
    ):
        crontab_data = structures.CrontabData(
            command=(
                "/home/user/.venv/bin/python "
                "-m postman_collection_exporter.cli "
                "archive "
                "--path-to-collections=path_to_archive "
                "--path-to-archive=archive_name "
                "--name=archive_name "
                "--archive-type=zip "
                "--log-path=/home/user/crontab/cron.log"
            ),
            comment="Some comment",
            pattern=pattern,
            user=getpass.getuser(),
        )
        crontab_helpers.set_cron_schedule(crontab_data)


@pytest.mark.asyncio
async def test_set_schedule_success() -> None:
    command = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    comment = "Test comment"
    pattern = "* * * * *"
    crontab_data = structures.CrontabData(
        command=command, comment=comment, pattern=pattern, user=getpass.getuser()
    )

    result = crontab_helpers.set_cron_schedule(crontab_data)
    assert result == (
        f"\nCommand  ==> {command}\n"
        f"Schedule ==> {pattern}\n"
        f"Comment  ==> {comment}\n"
        f"User     ==> {getpass.getuser()}\n"
    )

    output = subprocess.run(
        ["crontab", "-l"], check=True, capture_output=True, text=True
    ).stdout.strip("\n")

    assert command and comment in output

    remove_cron_job_by_comment(command)


@pytest.mark.asyncio
async def test_set_schedule_if_already_exists() -> None:
    comment = "Some comment"
    command = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    pattern = "* * * * *"
    user = getpass.getuser()
    crontab_data = structures.CrontabData(
        command=command, comment=comment, pattern=pattern, user=user
    )
    crontab_helpers.set_cron_schedule(crontab_data)

    with pytest.raises(
        exceptions.CronScheduleExistsError,
        match=re.escape(
            f"Crontab schedule is already exists for this command {command}. "
            f"Cron comment: {comment}. Pattern: {pattern}. "
            "You can remove it with command 'cron.remove_all(command=<command>)'."
        ),
    ):
        crontab_data = structures.CrontabData(
            command=command, comment=command, pattern=pattern, user=user
        )
        crontab_helpers.set_cron_schedule(crontab_data)

    remove_cron_job_by_comment(command)


@pytest.mark.asyncio
async def test_write_schedule_into_filename_success() -> None:
    command = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    comment = "Test comment"
    pattern = "* * * * *"

    with tempfile.NamedTemporaryFile(
        dir=Path(__file__).parent, encoding="utf-8", mode="w"
    ) as file:
        crontab_data = structures.CrontabData(
            command=command,
            comment=comment,
            pattern=pattern,
            user=getpass.getuser(),
            filename=Path(file.name),
        )

        result = crontab_helpers.set_cron_schedule(crontab_data)

        assert result == (
            f"\nCommand  ==> {command}\n"
            f"Schedule ==> {pattern}\n"
            f"Comment  ==> {comment}\n"
            f"User     ==> {getpass.getuser()}\n"
        )
        file_content = Path(file.name).read_text(encoding="utf-8")
        assert command and comment in file_content


# ----- Get Schedules -----


@pytest.mark.asyncio
async def test_get_schedule_by_pattern_success() -> None:
    command_1 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    comment_1 = "Comment for archive"
    pattern_1 = "* * * * *"  # !run every minute
    crontab_data = structures.CrontabData(
        command=command_1, comment=comment_1, pattern=pattern_1, user=getpass.getuser()
    )

    crontab_helpers.set_cron_schedule(crontab_data)

    command_2 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "export "
        "--path=path_to_export "
        "--collection-names=my_collection "
        "--log-path=/home/sergey/crontab/cron.log"
    )
    comment_2 = "Comment for export"
    pattern_2 = "0 * * * *"  # !run every hour
    crontab_data = structures.CrontabData(
        command=command_2, comment=comment_2, pattern=pattern_2, user=getpass.getuser()
    )
    crontab_helpers.set_cron_schedule(crontab_data)

    crons = list(
        job
        for job in crontab_helpers.get_cron_schedules(
            pattern="* * * * *", user=getpass.getuser()
        )
        if not str(job).startswith("#")
    )

    assert len(crons) == 1
    assert crons[0].command == command_1 and crons[0].comment == comment_1

    remove_cron_job_by_comment(comment_1)
    remove_cron_job_by_comment(comment_2)


@pytest.mark.asyncio
async def test_get_schedule_all() -> None:
    command_1 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    comment_1 = "Comment for archive"
    pattern_1 = "* * * * *"  # !run every minute
    crontab_data = structures.CrontabData(
        command=command_1, comment=comment_1, pattern=pattern_1, user=getpass.getuser()
    )

    crontab_helpers.set_cron_schedule(crontab_data)

    command_2 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "export "
        "--path=path_to_export "
        "--collection-names=my_collection "
        "--log-path=/home/sergey/crontab/cron.log"
    )
    comment_2 = "Comment for export"
    pattern_2 = "0 */5 * * *"  # !run every 5 hour
    crontab_data = structures.CrontabData(
        command=command_2, comment=comment_2, pattern=pattern_2, user=getpass.getuser()
    )
    crontab_helpers.set_cron_schedule(crontab_data)

    crons = list(
        job
        for job in crontab_helpers.get_cron_schedules(show_all=True)
        if not str(job).startswith("#")
        and job.comment in {"Comment for archive", "Comment for export"}
    )

    assert len(crons) == 2
    assert crons[0].command == command_1 and crons[0].comment == comment_1
    assert crons[1].command == command_2 and crons[1].comment == comment_2

    remove_cron_job_by_comment(comment_1)
    remove_cron_job_by_comment(comment_2)


@pytest.mark.asyncio
async def test_get_schedule_for_user() -> None:
    command_1 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "archive "
        "--path-to-collections=path_to_archive "
        "--path-to-archive=archive_name "
        "--name=archive_name "
        "--archive-type=zip "
        "--log-path=/home/user/crontab/cron.log"
    )
    comment_1 = "Comment for archive"
    pattern_1 = "* * * * *"  # !run every minute
    crontab_data = structures.CrontabData(
        command=command_1, comment=comment_1, pattern=pattern_1, user=getpass.getuser()
    )

    crontab_helpers.set_cron_schedule(crontab_data)

    command_2 = (
        "/home/user/.venv/bin/python "
        "-m postman_collection_exporter.cli "
        "export "
        "--path=path_to_export "
        "--collection-names=my_collection "
        "--log-path=/home/sergey/crontab/cron.log"
    )
    comment_2 = "Comment for export"
    pattern_2 = "0 */5 * * *"  # !run every 5 hour
    crontab_data = structures.CrontabData(
        command=command_2, comment=comment_2, pattern=pattern_2, user=getpass.getuser()
    )
    crontab_helpers.set_cron_schedule(crontab_data)

    crons = list(
        job
        for job in crontab_helpers.get_cron_schedules(user=getpass.getuser())
        if not str(job).startswith("#")
    )

    assert len(crons) == 2
    assert crons[0].command == command_1 and crons[0].comment == comment_1
    assert crons[1].command == command_2 and crons[1].comment == comment_2

    remove_cron_job_by_comment(comment_1)
    remove_cron_job_by_comment(comment_2)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "pattern",
    (
        "* * * *",
        "* * * * * *",
        "70 * * * *",
        "* 25 * * *",
        "* * 0 * *",
        "*/-5 * * * *",
        "*/* * * * *",
        "5-2 * * * *",
    ),
)
async def test_get_schedule_cron_pattern_invalid(pattern: str) -> None:
    crons_gen = crontab_helpers.get_cron_schedules(pattern)
    with pytest.raises(
        ValueError,
        match=re.escape(f"Cron pattern [{pattern}] isn't valid."),
    ):
        next(crons_gen)
