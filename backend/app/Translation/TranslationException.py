class PipelineException(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class PathNotExist(PipelineException):
    def __init__(self, message: str):
        super().__init__(message)


class AudioExtractionError(PipelineException):
    def __init__(self, message: str):
        super().__init__(message)


class TranscriptionError(PipelineException):
    def __init__(self, message: str):
        super().__init__(message)
