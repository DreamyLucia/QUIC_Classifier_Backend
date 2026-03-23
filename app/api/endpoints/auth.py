# app/api/endpoints/auth.py
from fastapi import APIRouter
from app.utils.response import APIResponse
from app.core.security import RSAUtil
from app.services import auth_service
from app.schemas.auth import RegisterRequest, LoginRequest, ResetRequest, AuthResponse, PublicKeyResponse

router = APIRouter(prefix="/users", tags=["认证"])


@router.get("/public-key", response_model=PublicKeyResponse)
def get_public_key():
    """获取 RSA 公钥"""
    try:
        public_key = RSAUtil.get_public_key_pem()
        return APIResponse.success(data={"publicKey": public_key})
    except Exception as e:
        return APIResponse.error(msg=str(e), code=500)


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """用户注册"""
    # 解密密码
    try:
        password = RSAUtil.decrypt_password(req.password)
    except Exception as e:
        return APIResponse.error(msg="密码解密失败", code=400)

    # 注册用户
    success, msg, token, user_id, username, role = auth_service.register(req.username, password)

    if not success:
        return APIResponse.error(msg=msg, code=400)

    return APIResponse.success(data={
        "token": token,
        "userId": user_id,
        "username": username,
        "role": role
    }, msg=msg)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """用户登录"""
    # 解密密码
    try:
        password = RSAUtil.decrypt_password(req.password)
    except Exception as e:
        return APIResponse.error(msg="密码解密失败", code=400)

    # 登录验证
    success, msg, token, user_id, username, role = auth_service.login(req.username, password)

    if not success:
        return APIResponse.error(msg=msg, code=401)

    return APIResponse.success(data={
        "token": token,
        "userId": user_id,
        "username": username,
        "role": role
    }, msg=msg)


@router.post("/reset")
def reset_password(req: ResetRequest):
    """重置密码"""
    # 解密新密码
    try:
        new_password = RSAUtil.decrypt_password(req.password)
    except Exception as e:
        return APIResponse.error(msg="密码解密失败", code=400)

    # 重置密码
    success, msg, token = auth_service.reset_password(req.username, new_password)

    if not success:
        return APIResponse.error(msg=msg, code=400)

    return APIResponse.success(data={"token": token}, msg=msg)