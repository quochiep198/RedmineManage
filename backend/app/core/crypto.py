from cryptography.fernet import Fernet

from app.core.config import settings


_fernet = Fernet(settings.redmine_fernet_key.encode("utf-8"))


def encrypt_secret(value: str) -> str:
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
