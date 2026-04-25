"""CashLab — Auth schemas"""
from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class SocialLoginRequest(BaseModel):
    """Login via Google ou Apple — frontend envia o id_token obtido via expo-auth-session"""
    provider: str  # "google" ou "apple"
    id_token: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    auth_provider: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}
