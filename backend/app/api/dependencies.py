from datetime import datetime
from fastapi import Request, HTTPException, Depends
from jose import jwt, JWTError
from app.core.settings import settings
from app.service.user import UserService

def get_token(request: Request):
    token = request.cookies.get('access_token')
    if not token:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return token


async def get_current_user(token: str = Depends(get_token)):
    try:
        payload = jwt.decode(token, settings.ACCESS_TOKEN_SECRET_KEY, algorithms=settings.ALGORITHM)
        expire: str = payload.get("exp")
        if not expire or int(expire) < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
        user_id = payload.get("sub")
        if not user_id: 
            raise HTTPException(status_code=401, detail="Invalid access token")
    
        user = await UserService.get_user_by_id(int(user_id))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except JWTError: 
        raise HTTPException(status_code=401, detail="Invalid access token")
    