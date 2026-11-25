from src.core.security import get_password_hash
from src.db.engine import get_session,async_session_factory, engine
from src.db.models import Base, User
from sqlalchemy import select
import asyncio

async def init():
    """初始化数据库: 创建所有表"""
    print("正在创建数据库表...")
    async with engine.begin() as conn:
        # Base 是从 declarative_base() 创建的基类
        # 它包含了所有模型的元数
        await conn.run_sync(Base.metadata.create_all)
    print("✅ 数据库表创建完成")


    # async with get_session() as session:

    async with async_session_factory() as session:
         result = await session.execute(
            select(User).where(User.email == "admin@campus.com")
        )
         
         if not result.scalar_one_or_none():
            admin = User(
                email="admin@campus.com",
                password_hash=get_password_hash("12345678"),
                role="admin",
            )
            session.add(admin)
            await session.commit()
            print("✅ 管理员已创建： admin@campus.com/ 12345678")
         else:
                print("ℹ  管理员已存在，跳过")

    await engine.dispose()
    print("🎉 初始化完成！")



if __name__ == "__main__":
    asyncio.run(init())


# uv run python -m scripts.init_db