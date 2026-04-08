from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.db import get_async_session
from src.core.security import hash_password, verify_password
from src.core.dependencies import create_access_token, create_refresh_token, get_current_user
from src.models.user import User
from src.schemas.user import UserCreate, UserLogin, Token, UserResponse

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register', response_model=Token)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(User).where(User.email == user_data.email) #type: ignore
    )

    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail='Email already registered')
    
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({'sub': str(user.id)})
    refresh_token = create_refresh_token({'sub': str(user.id)})

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

@router.post('/login', response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_async_session)
):
    result = await db.execute(
        select(User).where(User.email == credentials.email) #type: ignore
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Inactive user')
    
    access_token = create_access_token({'sub': str(user.id)})
    refresh_token = create_refresh_token({'sub': str(user.id)})

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }

@router.post('/refresh', response_model=Token)
async def refresh_token(refresh_token: str):
    from jose import JWTError, jwt
    from src.core.config import settings

    try:
        payload = jwt.decode(
            refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm_key]
        )
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get('me', response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user