from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
from app.utils.response import APIResponse
from app.schemas.user import UserInfoResponse

router = APIRouter(prefix="/users", tags=["用户信息"])


@router.get("/info", response_model=UserInfoResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    需要携带 Token
    """
    return APIResponse.success(data={
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    })
