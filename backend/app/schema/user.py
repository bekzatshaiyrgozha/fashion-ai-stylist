from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict


class SLogin(BaseModel):

    email: EmailStr
    password: str

class SUserRegistration(SLogin):
    first_name: str
    last_name: str

class SUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str
    last_name: str
    email: str
    is_admin: bool = False
