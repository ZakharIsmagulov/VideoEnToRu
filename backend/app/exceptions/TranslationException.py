class PipelineException(Exception):
    pass

class PathNotExist(PipelineException):
    pass

class AudioExtractionError(PipelineException):
    pass

class TranscriptionError(PipelineException):
    pass

class TranslationStopped(PipelineException):
    pass
