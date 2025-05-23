import inspect
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable


def setup_cli_logging(
    level: int, propagate: bool = True, logger: logging.Logger | None = None
) -> Callable[..., Callable[..., None]]:
    """
    Decorator factory for setting up logging configuration for a CLI command.

    This decorator expects the decorated function to receive a 'log_path' keyword argument,
    which specifies the path to the log file.

    If a custom logger is provided and propagate is set to False, the decorator disables propagation
    for that logger, so only messages from that logger will be written to the log file (not messages
    from other libraries or modules).

    Args:
        level (int): Logging level (e.g., logging.INFO).
        propagate (bool, optional): Whether to propagate log messages to the root logger. Defaults to True.
        logger (logging.Logger | None, optional): Custom logger to control propagation. Defaults to None.

    Returns:
        Callable: A decorator that wraps a function, sets up logging, and then calls the function.
    """

    def decorator(func: Callable[..., None]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any | None:
            log_path = kwargs.pop("log_path", None)
            if log_path is None:
                raise TypeError(
                    f"Missing required 'log_path' keyword argument in '{func.__name__}' command. "
                    "Make sure your Click command includes a '--log-path' option as Path type."
                )

            if not Path(log_path).exists():
                Path(log_path).parent.mkdir(parents=True, exist_ok=True)
                Path(log_path).touch()

            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(
                logging.Formatter(
                    "[%(levelname)s - %(asctime)s] - %(name)s - [%(message)s]",
                    datefmt="%Y-%m-%d %H:%M:%S",
                    style="%",
                )
            )

            # check if a handler for this file already exists before adding it
            if not any(
                isinstance(handler, logging.FileHandler)
                and handler.baseFilename == str(log_path)
                for handler in logging.root.handlers
            ):
                logging.root.addHandler(file_handler)

            logging.root.setLevel(level)

            if logger is not None and not propagate:
                logger.propagate = False

            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)

            return func(*args, **kwargs)

        return wrapper

    return decorator
