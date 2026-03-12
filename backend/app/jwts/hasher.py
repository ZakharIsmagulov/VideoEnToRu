import bcrypt


def hash_pass(password: str) -> str:
    salt = bcrypt.gensalt()
    pass_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(pass_bytes, salt)
    return hashed.decode("utf-8")


def verify_pass(password: str, hashed: str) -> bool:
    pass_bytes = password.encode("utf-8")
    hashed_bytes = hashed.encode("utf-8")

    return bcrypt.checkpw(pass_bytes, hashed_bytes)