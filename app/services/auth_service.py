import bcrypt
import jwt
import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User


def hash_password(password: str) -> str:
    """哈希密码"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def generate_token(username: str) -> str:
    """生成 JWT token"""
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        "iat": datetime.datetime.utcnow()
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_user_by_username(db: Session, username: str):
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def register(username: str, password: str):
    """
    用户注册
    Returns: (success: bool, msg: str, token: str or None)
    """
    db = SessionLocal()
    try:
        # 检查用户名是否存在
        existing_user = get_user_by_username(db, username)
        if existing_user:
            return False, "用户名已存在", None

        # 创建新用户
        new_user = User(
            username=username,
            password=hash_password(password)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # 生成 token
        token = generate_token(username)

        return True, "注册成功", token

    except Exception as e:
        db.rollback()
        print(f"注册失败: {e}")
        return False, "注册失败，请重试", None
    finally:
        db.close()


def login(username: str, password: str):
    """
    用户登录
    Returns: (success: bool, msg: str, token: str or None)
    """
    db = SessionLocal()
    try:
        # 查找用户
        user = get_user_by_username(db, username)
        if not user:
            return False, "用户名或密码错误", None

        # 验证密码
        if not verify_password(password, user.password):
            return False, "用户名或密码错误", None

        # 生成 token
        token = generate_token(username)

        return True, "登录成功", token

    except Exception as e:
        print(f"登录失败: {e}")
        return False, "登录失败，请重试", None
    finally:
        db.close()


def reset_password(username: str, new_password: str):
    """
    重置密码
    Returns: (success: bool, msg: str, token: str or None)
    """
    db = SessionLocal()
    try:
        # 查找用户
        user = get_user_by_username(db, username)
        if not user:
            return False, "用户不存在", None

        # 更新密码
        user.password = hash_password(new_password)
        db.commit()

        # 重新生成 token
        token = generate_token(username)

        return True, "密码重置成功", token

    except Exception as e:
        db.rollback()
        print(f"重置密码失败: {e}")
        return False, "重置密码失败，请重试", None
    finally:
        db.close()