import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse


from src.core.deps import get_current_user, get_db
from src.config import settings
from src.db.models import User
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageItem,
    SessionDetailResponse,
    SessionItem,
    SessionListResponse,
    SourceItem,
)
from src.services.chat import (
    create_session,
    delete_session,
    get_session_detail,
    get_user_sessions,
    process_question,
)

router = APIRouter()

@router.post("/sessions", status_code=201)
async def new_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新会话"""
    session = await create_session(str(current_user.id), db)
    return {"session_id": str(session.id), "title": session.title}

@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户所有会话"""

    sessions = await get_user_sessions(str(current_user.id), db)

    return SessionListResponse(sessions=[
        SessionItem(
            id=str(s.id),
            title=s.title,
            created_at=s.created_at,
        )
        for s in sessions
    ])


@router.delete("/sessions/{session_id}")
async def remove_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    
    await delete_session(session_id, db)
    return {"message": "ok"}

@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取会话详情"""
    messages = await get_session_detail(session_id, db)

    # print('messages:--', messages)

    return SessionDetailResponse(
       messages = [
           MessageItem(
               role=m.role,
               content=m.content,
               created_at=m.created_at,
               sources=[SourceItem(**s) for s in (m.sources or [])] if settings.SHOW_SOURCE else [],
            #    sources=[SourceItem(**s) for s in (m.sources or [])],
           )
           for m in messages
       ] 
    )
    

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """问答:非流式"""
    response = await process_question(session_id=request.session_id, question=request.question, db=db)
    answer = response["answer"]
    # dict to SourceItem实例
    # 字典字段恰好和SourceItem模型字段对应
    sources = [ SourceItem(**s) for s in response.get("sources", [])]

    return ChatResponse(answer=answer, sources=sources)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """问答:流式输出 SSE协议： server-sent events
    token 事件
    source 事件
    done 事件：表示回答完成
    
    """
    from src.rag.vector_store import get_vector_store
    from src.rag.chain import get_llm

    from src.rag.chain import format_docs
    from langchain_core.prompts import ChatPromptTemplate
    import asyncio

    vector_store = get_vector_store()


    async def event_generator():

        # 知识检索（问题）
        docs_with_scores = vector_store.similarity_search_with_score(request.question, k=settings.RETRIEVER_TOP_K)
        docs = [doc for doc, _ in docs_with_scores]
        context = format_docs(docs)

        # 构建提示词&调用LLM
        llm = get_llm()
        SYSTEM_PROMPT = """你是一个校园生活助手，请严格遵循以下规则：

            1. 仅基于提供的上下文内容回答问题
            2. 如果上下文不足以回答，如实说明"文档中没有相关信息"，不要编造
            3. 使用中文回答，语言简洁易懂
            4. 涉及数字、时间、地点等信息时，引用原文

            上下文：
            {context}"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ])

        chain = prompt | llm

        # 流式输出(token) & 推送前端
        answer_parts = []
        async for chunk in chain.astream({"context": context, "input": request.question}):
            content  = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                answer_parts.append(content)
                # SSE协议：token事件
                yield {"data":json.dumps({"type":"token","content":content})}
        
        # 检索来源source & 推送前端
        sources = []
        if settings.SHOW_SOURCE:
              for i, doc in enumerate(docs):
                score = docs_with_scores[i][1] if i < len(docs_with_scores) else 0.0
                sources.append({
                    "content": doc.page_content[:200],       # 只截取前 200 字
                    "chapter": doc.metadata.get("chapter", ""),
                    "section": doc.metadata.get("section", ""),
                    "score": round(score, 4),               # 相关性评分，保留 4 位小数
                })
        # 将来源信息推送给前端
        yield {"data": json.dumps({"type": "sources", "content": sources})}

        #流式输出结束 & 推送前端
        yield {"data": json.dumps({"type": "done"})}


        #异步保存问答消息同步到数据库
        # ensure_future ：后台执行 不阻塞SSE 响应返回
        asyncio.ensure_future(
            _save_chat(request.session_id, request.question, answer_parts, sources))


    #event_generator() 返回：事件流内容
    # EventSourceResponse：返回事件流内容响应
    # 匹配SSE协议：text/event-stream
    return EventSourceResponse(event_generator())



async def _save_chat(session_id: str, question: str, answer, sources: list):
    from src.db.engine import async_session_factory
    from src.db.models import Message, Session
    from sqlalchemy import select

    async with async_session_factory() as db:
        user_msg = Message(
            session_id=session_id,
            role="user",
            content=question,
        )
        db.add(user_msg)

        # 核心修复：如果answer是列表，拼接成完整字符串
        answer_text = "".join(answer) if isinstance(answer, list) else answer
        assistant_msg = Message(
            session_id=session_id,
            role="assistant",
            content=answer_text,
            sources=sources,
        )
        db.add(assistant_msg)

        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session and session.title == "新对话":
            session.title = question[:30]

        await db.commit()

        

