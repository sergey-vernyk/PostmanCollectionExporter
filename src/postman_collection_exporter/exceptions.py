class PostmanAPIError(Exception):
    """Base class for all Postman-related exceptions."""


class EnvironmentVariableMissingError(EnvironmentError):
    """Exception raised when there is environment variable is not found."""


class PostmanCollectionRetrievalError(PostmanAPIError):
    """Exception raised when there is an error retrieving a Postman collection."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(
            f"Error occurred while getting collection. Status: {status_code}."
        )


class PostmanAuthenticationError(PostmanAPIError):
    """Exception raised when there is an authentication error with the Postman API."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PostmanTooManyRequestsError(PostmanAPIError):
    """Exception raised when the Postman API rate limit is exceeded (HTTP 429)."""

    def __init__(self) -> None:
        super().__init__("To many requests to API. Try again later.")


class PostmanResponseMissingKeyError(PostmanAPIError):
    """Exception raised when a required key is missing in the Postman API response."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Response with collection does not have key '{key}'.")


class PostmanCollectionNotFoundError(PostmanAPIError):
    """Exception raised when a Postman collection with the specified name is not found."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Collection not found with provided name: '{name}'.")


class ArchiveCreateError(RuntimeError):
    """Raised when archiving the Postman collections fails."""


class CronScheduleExistsError(Exception):
    """Raised when schedule is already exists in crontab."""

    def __init__(self, pattern: str, comment: str, command: str) -> None:
        self.pattern = pattern
        self.comment = comment
        self.command = command
        super().__init__(
            f"Crontab schedule is already exists for this command {command}. "
            f"Cron comment: {comment}. Pattern: {pattern}. "
            "You can remove it with command 'cron.remove_all(command=<command>)'."
        )
