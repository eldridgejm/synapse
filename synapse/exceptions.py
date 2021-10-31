class Error(Exception):
    pass


class NetworkKeyError(Error):
    """The key does not exist."""
