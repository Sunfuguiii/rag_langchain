from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Message, Session
from src.rag.chain import ask_question



async def create_session(user_id: str, db: AsyncSession) -> Session:
    """创建会话"""

    session = Session(
        user_id=user_id,
        title="新对话",
    )
    db.add(session)
    await db.flush()
    return session


async def get_user_sessions(user_id: str, db: AsyncSession) -> list[Session]:
    """获取用户所有会话"""
    result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
    )
    return list(result.scalars().all())


async def get_session_detail(session_id: str, db: AsyncSession) -> list[Message]:
    """获取会话详情:返回会话下的所有消息"""

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())

async def delete_session(session_id: str, db: AsyncSession):
    """删除会话"""
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session:
        await db.delete(session)


async def process_question(
    session_id: str,
    question: str,
    db: AsyncSession,
) -> dict:
    
    """用户问题-消息"""
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=question,
    )
    db.add(user_msg)


    # 获取会话历史消息
    history = await get_session_detail(session_id, db)
    history_msgs = [
        {
            "role": m.role,
            "content": m.content,
        }
        for m in history[:-1]
    ]
 

    # rag 回答用户问题
    response = await ask_question(question, history_msgs)
    print(f'rag 回答用户问题:', response)


    # 保存AI回答消息
    ai_msg = Message(
        session_id=session_id,
        role="assistant",
        content=response["answer"],
        sources=response.get("sources", []),
    )
    db.add(ai_msg)

    # 会话标题优化
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )

    session = session_result.scalar_one_or_none()
    if session and session.title == "新对话":
        session.title = question[:30]


    return response
   
    
