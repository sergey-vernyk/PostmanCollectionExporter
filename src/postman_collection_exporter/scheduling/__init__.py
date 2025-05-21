import warnings

try:
    import crontab
except ImportError:
    warnings.warn(
        "The 'python-crontab' package is required for scheduling functionality. "
        "Install it using 'pip install python-crontab'.",
        UserWarning,
    )
