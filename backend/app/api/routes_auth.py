from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    role: str
    user_id: str

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    return LoginResponse(token="demo_token", role="CEO", user_id="u_001")
