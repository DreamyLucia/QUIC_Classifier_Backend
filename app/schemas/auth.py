# app/schemas/auth.py
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str  # RSA 加密后的密码


class LoginRequest(BaseModel):
    """登录请求"""
    username: str
    password: str  # RSA 加密后的密码


class ResetRequest(BaseModel):
    """重置密码请求"""
    username: str
    password: str  # 新密码（RSA 加密后）


class AuthResponse(BaseModel):
    """登录/注册响应"""
    token: str
    userId: str
    username: str
    role: str


class PublicKeyResponse(BaseModel):
    """公钥响应"""
    publicKey: str
