class KuroError(Exception):
    def __init__(self, message="", suggestion=""):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self):
        return self.message


class ResolutionError(KuroError): ...


class PlayerNotFoundError(KuroError): ...


class StreamError(KuroError): ...


class DownloadError(KuroError): ...
