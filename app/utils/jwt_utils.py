import jwt
import datetime
from typing import Optional, Dict, Any
from app.core.config import settings


def create_jwt_token(username: str, expires_hours: int = None) -> str:
    """
    生成 JWT token

    Args:
        username: 用户名
        expires_hours: 过期时间（小时），默认使用配置中的值

    Returns:
        JWT token 字符串
    """
    if expires_hours is None:
        expires_hours = settings.JWT_EXPIRATION_HOURS

    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=expires_hours),
        "iat": datetime.datetime.utcnow(),  # 签发时间
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        验证成功返回 payload，失败返回 None
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        print("Token 已过期")
        return None
    except jwt.InvalidTokenError:
        print("Token 无效")
        return None
    except Exception as e:
        print(f"Token 验证失败: {e}")
        return None


def get_username_from_token(token: str) -> Optional[str]:
    """
    从 token 中获取用户名

    Args:
        token: JWT token 字符串

    Returns:
        用户名，验证失败返回 None
    """
    payload = verify_jwt_token(token)
    if payload:
        return payload.get("username")
    return None