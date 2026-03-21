import secrets


def generate_jwt_secret(length: int = 32) -> str:
    """
    生成一个安全的 JWT_SECRET

    Args:
        length: 密钥长度（字符数），默认 32

    Returns:
        随机生成的密钥字符串
    """
    # 使用 secrets 模块生成密码学安全的随机字符串
    secret = secrets.token_urlsafe(length)
    return secret


if __name__ == "__main__":
    print("🔐 JWT_SECRET 生成器")
    print("=" * 60)

    secret = generate_jwt_secret(32)

    print(f"JWT_SECRET={secret}")