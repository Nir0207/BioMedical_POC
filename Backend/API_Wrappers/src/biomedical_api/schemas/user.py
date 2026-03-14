from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PostgresSummaryResponse(BaseModel):
    user_count: int


class GraphSummaryResponse(BaseModel):
    nodes: int
    relationships: int
