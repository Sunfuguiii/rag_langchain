from itertools import chain

from src.config import settings

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

from src.rag import vector_store
from src.rag.vector_store import get_vector_store

# 核心流程：
#   用户问题 → 向量检索 → 文档拼接 → Prompt + LLM → 答案 + 来源


SYSTEM_PROMPT = """你是一个校园生活助手，请严格遵循以下规则：

1. 仅基于提供的上下文内容回答问题
2. 如果上下文不足以回答，如实说明"文档中没有相关信息"，不要编造
3. 使用中文回答，语言简洁易懂
4. 涉及数字、时间、地点等信息时，引用原文

上下文：
{context}"""


def get_llm() -> BaseLanguageModel:
    """获取语言模型：根据配置文件选择不同的模型"""

    provider = settings.LLM_PROVIDER

    if provider == "deepseek":
        return ChatOpenAI(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.5,
            max_retries=3,
        )
    # elif provider == "openai":
    #     return ChatOpenAI(
    #         model=settings.OPENAI_MODEL,
    #         api_key=settings.OPENAI_API_KEY,
    #         base_url=settings.OPENAI_API_BASE_URL,
    #         temperature=0.5,
    #         max_retries=3,
    #     )

    # 默认：Ollama 本地模型
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1
    )

def format_docs(docs):
    """格式化文档：将文档列表转换为字符串，每个文档占一行"""
    return "\n\n".join(doc.page_content for doc in docs)

# 返回值 :dict
#   {"answer": "答案内容", "source": ["文档1", "文档2", "文档3..."]}
async def ask_question(question: str, history: list | None = None) -> dict:
    """回答用户问题：根据用户问题和历史记录，调用语言模型生成答案"""

    llm = get_llm()
    vector_store = get_vector_store()


    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history",optional=True), # 可选历史记录
        ("human", "{input}"),
    ])

    # 检索
    docs_with_scores = vector_store.similarity_search_with_score(question, k=settings.RETRIEVER_TOP_K)
    docs = [doc for doc, _ in docs_with_scores]

    print(f'检索到的docs:', docs)

    # 提示词 =>LLM =>流式输出

    # 链 :输入dict=>自动填充prompt中的变量=>调用llm=>返回输出
    chain = prompt | llm | StrOutputParser()

    answer = await chain.ainvoke({
        "context": format_docs(docs),
        "input": question,
        "chat_history": history or [],
    })

    print(f'生成的答案:', answer)
    #来源 :文档标题列表
    sources = []
    for i, doc in enumerate(docs):
        score = docs_with_scores[i][1] if i < len(docs_with_scores) else 0.0
        sources.append({
            "content": doc.page_content[:100],          # 截取前200字符供预览
            "chapter": doc.metadata.get("chapter", ""),  # 所属章节
            "section": doc.metadata.get("section", ""),  # 所属小节
            "score": round(score, 4),                    # 相关度评分（越小越相关）
        })

    return {
        "answer": answer,
        "sources": sources,
    }






