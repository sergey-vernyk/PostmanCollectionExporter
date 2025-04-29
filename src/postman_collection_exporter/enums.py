from enum import StrEnum


class ArchiveType(StrEnum):
    """Type of archives used for archiving collections."""

    TAR = "tar"
    ZIP = "zip"
    GZTAR = "gztar"
    BZTAR = "bztar"
    XZTAR = "bztar"
