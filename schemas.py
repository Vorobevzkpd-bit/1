from pydantic import BaseModel

class LoginRequest(BaseModel):
    full_name: str
    password: str