from pydantic import BaseModel, EmailStr


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequestSchema(BaseModel):
    refresh_token: str
