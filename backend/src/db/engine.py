from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.db.models import Base
from src.config import settings


# 创建异步数据库引擎
# print(f"""settings.DATABASE_URL: {settings.DATABASE_URL}""")
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)


# 创建异步会话工厂
# engine 异步数据库引擎
# expire_on_commit 是否在提交事务后过期会话中的对象
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """初始化数据库: 创建所有表"""
    async with engine.begin() as conn:
        # Base 是从 declarative_base() 创建的基类
        # 它包含了所有模型的元数
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """关闭数据库引擎"""
    await engine.dispose()


async def get_session():
    """获取异步数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()  # 提交事务
        except Exception as e:
            await session.rollback()  # 回滚事务
            raise e
        finally:
            await session.close()  # 关闭会话
