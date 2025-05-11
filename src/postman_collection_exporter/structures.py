from dataclasses import dataclass
from pathlib import Path


@dataclass
class CrontabData:
    """Represents data for configure crontab schedule."""

    command: str
    comment: str
    pattern: str
    user: bool | str
    filename: Path | None = None
