import sys
from pathlib import Path

import asyncclick as click

from ..dependencies.utils import ensure_crontab_is_installed


def compose_cron_command(command_name: str, params: list[str], module_name: str) -> str:
    """Composes and returns command for inserting it into crontab file."""
    py_exec_path = Path(sys.executable)
    return f"{py_exec_path} -m {module_name} {command_name} {' '.join(params)}"


class CrontabParamType(click.ParamType):
    """
    Custom click parameter that represents crontab schedule.
    Examples: `* * * * *`, `0 */4 * * *`, etc.
    """

    name = "crontab"

    def convert(
        self, value: str, param: click.Parameter | None, ctx: click.Context | None
    ) -> str:
        # pylint: disable=import-outside-toplevel
        ensure_crontab_is_installed()
        import crontab

        if crontab.CronSlices.is_valid(value):
            return value

        self.fail(f"{value!r} is not a valid crontab pattern.", param, ctx)


CRONTAB_PATTERN = CrontabParamType()
