from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from app.auth.auth import AuthService
from app.api.dependencies import get_current_user
from app.schema.user import SUserResponse

router = APIRouter()


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
async def register(req: RegisterRequest):
    # delegate to AuthService which uses UserService / DAO
    return await AuthService.register(first_name=req.first_name, last_name=req.last_name, email=req.email, password=req.password)


@router.post("/login")
async def login(response: Response, req: LoginRequest):
    return await AuthService.login(response=response, email=req.email, password=req.password)


@router.get("/profile", response_model=SUserResponse)
async def get_profile(user=Depends(get_current_user)):
    return user


@router.put("/profile", response_model=SUserResponse)
async def update_profile(data: SUserResponse, user=Depends(get_current_user)):
    # TODO: implement update logic
    return data
