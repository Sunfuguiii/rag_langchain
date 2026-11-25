
from src.db.engine import get_session
from fastapi import Depends, status, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.security import verify_token
from src.db.models import User
from sqlalchemy import select


#自动解析Authorization头 提取token
# 如果Authorization头中没有token 则会抛出HTTPException
bearer = HTTPBearer()


async def get_db():
    """数据库会话依赖"""
    #  get_session ：AsyncGenerator[AsyncSession, Any] 类型
    async for session in get_session():
        yield session

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer),
        db:Session= Depends(get_db)):
    """获取当前用户"""

    access_token = credentials.credentials
    # credentials_scheme = credentials.scheme

    try:
        payload = verify_token(access_token)
        print('payload:-----------', payload)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    return user

   
# 有些接口不仅需要登录 而且还需要有管理员权限
async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """管理员权限依赖"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
