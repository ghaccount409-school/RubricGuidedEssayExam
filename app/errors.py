"""Application errors surfaced to the UI."""


class TogetherApiError(Exception):
    """Together.ai HTTP API returned an error (e.g. 401 invalid key)."""

    def __init__(self, message: str, http_status: int = 503):
        self.message = message
        self.http_status = http_status
        super().__init__(message)
