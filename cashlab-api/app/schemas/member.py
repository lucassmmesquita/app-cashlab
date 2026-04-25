from __future__ import annotations
"""CashLab — Member schemas"""
from typing import Optional

from pydantic import BaseModel


class MemberCreate(BaseModel):
    name: str
    color: Optional[str] = None
    avatar_url: Optional[str] = None


class MemberResponse(BaseModel):
    id: int
    name: str
    color: Optional[str]
    avatar_url: Optional[str]

    model_config = {"from_attributes": True}
