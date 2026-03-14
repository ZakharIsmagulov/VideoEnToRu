class DBException(Exception):
    pass

class NoSessionProvided(DBException):
    pass

class UserException(DBException):
    pass

class UserAlreadyExist(UserException):
    pass

class UserNotFound(UserException):
    pass

class WrongPassword(UserException):
    pass

class VideoInstanceException(DBException):
    pass

class VideoNotFound(VideoInstanceException):
    pass

class JobIdNotFound(VideoInstanceException):
    pass

class RefreshException(DBException):
    pass

class RefreshNotFound(RefreshException):
    pass

class RefreshInactive(RefreshException):
    pass

class RefreshExpired(RefreshException):
    pass

class RefreshRevoked(RefreshException):
    pass
