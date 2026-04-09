from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
 
from src.core.db import get_async_session
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix='/users', tags=['users'])

@router.get('/{user_id}', response_model=UserResponse)
async def get_user(user_id: UUID, db: AsyncSession = Depends(get_async_session)) -> User:
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

    return user

@router.patch('/{user_id}', response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    
    if user_update.email and user_update.email != user.email:
        result = await db.execute(
            select(User).where(User.email == user_update.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        
        user.email = user_update.email
    
    if user_update.full_name:
        user.full_name = user_update.full_name
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user