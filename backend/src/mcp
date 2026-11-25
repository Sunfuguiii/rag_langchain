
# mcp 服务 ： 提供 mcp 协议的接口 
# 作用 ：给客户端claude提供 mcp 协议的接口，用于与 rag 服务进行通信

from mcp.server.fastmcp import FastMCP
from src.rag.chain import ask_question
from src.rag.vector_store import get_qdrant_client
from src.config import settings

mcp = FastMCP(
    name="Campus RAG System",
    instructions="""你是一个 RAG 知识库助手，可以检索校园相关文档（宿舍、食堂、选课、图书馆等）。

工具：
  - rag_query   向知识库提问，返回基于检索增强生成的回答
  - list_documents  列出知识库中所有文档
"""
)

@mcp.tool(name="rag_query", description="向知识库提问，返回基于检索增强生成的回答")
async def rag_query(question: str) -> dict:

    """向知识库提问，返回基于检索增强生成的回答"""

    if not question.strip():
        return {"answer": "请输入有效问题。", "sources": []}
    
    response = await ask_question(question)
    return response


@mcp.tool(description="列出知识库中的所有文档")
async def list_documents() -> list[str]:

    client = get_qdrant_client()

   #    facet 根据指定的集合和字段进行分面查询
    # documents = client.facet(
    #     collection_name=settings.QDRANT_COLLECTION,
    #     key="source",
    #     limit=1000,
    #     offset=0,
    # )


    # return documents

    return client.get_collections()
    