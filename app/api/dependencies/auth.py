import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.models.user import User
from app.services.auth_service import get_user_by_username
from app.core.database import SessionLocal

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    验证 JWT Token，返回 payload

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        解码后的 payload

    Raises:
        HTTPException: Token 无效或过期
    """
    token = credentials.credentials

    try:
        # 解码并验证签名
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


def get_current_user(payload: dict = Depends(verify_token)) -> User:
    """
    从 Token 获取当前用户

    Args:
        payload: verify_token 返回的 payload

    Returns:
        当前用户对象

    Raises:
        HTTPException: 用户不存在
    """
    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Token 中缺少用户名")

    db = SessionLocal()
    try:
        user = get_user_by_username(db, username)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        return user
    finally:
        db.close()
