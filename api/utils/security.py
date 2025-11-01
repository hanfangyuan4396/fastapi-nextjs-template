from typing import Final

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

# 采用 argon2id（PasswordHasher 默认即为 argon2id），参数取库默认的安全值
_HASHER: Final[PasswordHasher] = PasswordHasher()


def hash_password(password: str) -> str:
    """
    对明文密码进行哈希，返回安全的哈希字符串。

    Args:
        password: 明文密码，必须为非空字符串。

    Returns:
        适用于持久化存储的密码哈希（包含盐）。

    Raises:
        ValueError: 当 password 非法（空字符串或非 str）时抛出。
    """
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    # Argon2 会自动生成随机盐并编码到返回字符串中
    return _HASHER.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    校验明文密码是否与给定哈希匹配。

    Args:
        plain_password: 待校验的明文密码。
        password_hash: 已存储的密码哈希。

    Returns:
        当明文密码匹配哈希时返回 True，否则 False。
    """
    if not isinstance(plain_password, str) or not isinstance(password_hash, str):
        return False
    if not plain_password or not password_hash:
        return False
    try:
        return _HASHER.verify(password_hash, plain_password)
    except (argon2_exceptions.VerifyMismatchError, argon2_exceptions.InvalidHash):
        return False
    except Exception:
        return False
