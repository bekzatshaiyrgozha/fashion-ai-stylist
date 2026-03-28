from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr
from app.auth.auth import AuthService
from app.api.dependencies import get_current_user
from app.schema.user import SUserResponse
from sqlalchemy import select, func
from app.db.db_config import async_session_maker
from app.db.models.user import User

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


@router.post("/logout")
async def logout(response: Response):
    return await AuthService.logout(response=response)


@router.post("/bootstrap-admin")
async def bootstrap_admin(current_user=Depends(get_current_user)):
    """Promote the first user to admin. If admin already exists, only admins can call this."""
    async with async_session_maker() as session:
        admins_count = await session.scalar(
            select(func.count()).select_from(User).where(User.is_admin.is_(True))
        )

        # if at least one admin exists, disallow non-admin users
        if (admins_count or 0) > 0 and not getattr(current_user, "is_admin", False):
            raise HTTPException(status_code=403, detail="Admins only")

        row = await session.get(User, current_user.id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")

        row.is_admin = True
        await session.commit()
        await session.refresh(row)
        return {"message": "Admin granted", "email": row.email, "is_admin": True}


@router.get("/profile", response_model=SUserResponse)
async def get_profile(user=Depends(get_current_user)):
    return user


@router.put("/profile", response_model=SUserResponse)
async def update_profile(data: SUserResponse, user=Depends(get_current_user)):
    """Update user profile (first_name, last_name only - email and password via separate endpoints)"""
    async with async_session_maker() as session:
        row = await session.get(User, user.id)
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only allow updating name fields
        if data.first_name:
            row.first_name = data.first_name
        if data.last_name:
            row.last_name = data.last_name
        
        await session.commit()
        await session.refresh(row)
        
        return SUserResponse(
            id=row.id,
            email=row.email,
            first_name=row.first_name,
            last_name=row.last_name,
            is_admin=row.is_admin
        )
