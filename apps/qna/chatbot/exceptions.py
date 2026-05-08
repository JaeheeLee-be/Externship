class GroqAPIError(Exception):
    pass


class GroqTimeoutError(GroqAPIError):
    pass
