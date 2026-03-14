class APIException(Exception):
    pass

class NoFilenameException(APIException):
    pass

class VideotypeNotAllowed(APIException):
    pass

class VideoExtensionNotAllowed(APIException):
    pass

class CannotUploadFile(APIException):
    pass

class VideoUnprocessed(APIException):
    pass
