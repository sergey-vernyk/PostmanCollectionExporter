def ensure_crontab_is_installed() -> None:
    """Tries to import `python-crontab` package or raise `RuntimeError` otherwise."""
    try:
        import crontab  # pylint: disable=import-outside-toplevel
    except ImportError as e:
        raise RuntimeError(
            "The 'python-crontab' package is required for scheduling functionality. "
            "Install it using 'pip install python-crontab'."
        ) from e
