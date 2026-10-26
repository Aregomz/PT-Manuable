from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionResponse(BaseModel):
    username: str
