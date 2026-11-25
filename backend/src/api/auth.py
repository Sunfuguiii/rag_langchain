from fastapi import APIRouter, Depends, status, HTTPException

from src.core.deps import get_db, get_current_user
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    verify_token
    )

from src.db.models import User
from src.schemas.auth import (
    RegisterRequest, 
    UserResponse, 
    LoginRequest, 
    TokenResponse, 
    RefreshRequest)


router = APIRouter()




@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # 密码强度校验
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
    )
    print("注册用户--之前", user)
    db.add(user)
    await db.flush()  # 刷新数据库会话，确保 ID 被分配
    print("注册用户--之后", user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest):

    """刷新访问令牌"""
    # 验证刷新令牌
    try:
        payload = verify_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user_id = payload.get("sub")

    access_token = create_access_token({"sub": user_id})

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
    )
  


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
    )

