class DBException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UserException(DBException):
    def __init__(self, message: str):
        super().__init__(message)


class UserAlreadyExist(UserException):
    def __init__(self, message: str):
        super().__init__(message)


class UserNotFound(UserException):
    def __init__(self, message: str):
        super().__init__(message)


class WrongPassword(UserException):
    def __init__(self, message: str):
        super().__init__(message)


class RefreshException(DBException):
    def __init__(self, message: str):
        super().__init__(message)


class RefreshNotFound(RefreshException):
    def __init__(self, message: str):
        super().__init__(message)


class RefreshInactive(RefreshException):
    def __init__(self, message: str):
        super().__init__(message)


class RefreshExpired(RefreshException):
    def __init__(self, message: str):
        super().__init__(message)


class RefreshRevoked(RefreshException):
    def __init__(self, message: str):
        super().__init__(message)
