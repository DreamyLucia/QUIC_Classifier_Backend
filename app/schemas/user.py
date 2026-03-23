from pydantic import BaseModel


class UserInfoResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: str
