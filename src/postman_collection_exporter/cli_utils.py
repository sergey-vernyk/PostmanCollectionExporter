import sys
from pathlib import Path
from typing import Any

import asyncclick as click
import crontab


def compose_cron_command(command_name: str, params: list[str]) -> str:
    """Composes and returns command for inserting it into crontab file."""
    py_exec_path = Path(sys.executable)
    module_exec_path = __name__
    return f"{py_exec_path} -m {module_exec_path} {command_name} {' '.join(params)}"


class CrontabParamType(click.ParamType):
    """
    Custom click parameter that represents crontab schedule.
    Examples: `* * * * *`, `0 */4 * * *`, etc.
    """

    name = "crontab"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> str | None:
        try:
            if isinstance(value, str) and crontab.CronSlices.is_valid(value):
                return value
        except ValueError:
            self.fail(f"{value!r} is not a valid crontab pattern.", param, ctx)


CRONTAB_PATTERN = CrontabParamType()
