import pytest

from utils import hash_password, verify_password


def test_hash_and_verify() -> None:
    plain = "S3cure-P@ssw0rd"
    hashed = hash_password(plain)
    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_random_salt_hashes_differ() -> None:
    plain = "repeatable"
    h1 = hash_password(plain)
    h2 = hash_password(plain)
    # bcrypt 含随机盐：同一明文两次哈希不应相等
    assert h1 != h2
    # 两个哈希均可被各自验证通过
    assert verify_password(plain, h1) is True
    assert verify_password(plain, h2) is True


def test_empty_values_behavior() -> None:
    # 空字符串哈希应抛出异常
    with pytest.raises(ValueError, match="password must be a non-empty string"):
        hash_password("")

    # 空明文匹配真实哈希应返回 False
    valid_hash = hash_password("x")
    assert verify_password("", valid_hash) is False

    # 非空明文配空哈希应返回 False
    assert verify_password("x", "") is False
