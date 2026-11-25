from qdrant_client import QdrantClient
from qdrant_client.models import Payload, PointStruct, VectorParams, Distance

from src.config import settings

from src.rag.embeddings import get_embeddings
from langchain_qdrant import QdrantVectorStore


def get_qdrant_client() -> QdrantClient:

    client = QdrantClient(
        url=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT
    )

    return client

def get_vector_store() -> QdrantVectorStore:

    client = get_qdrant_client()
    # 判断集合是否存在
    exists = client.collection_exists(settings.QDRANT_COLLECTION)
    if not exists:
          # 如果 不存储在则创建
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=settings.QDRANT_VECTOR_SIZE, distance=Distance.COSINE),
            )
    
    
    embeddings = get_embeddings()

    # 封装：QdrantClient + 集合名称 + 嵌入模型
    return QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION, # 集合名称 必须与创建时一致
        embedding=embeddings,
    )


async def index_documents(chunks: list) -> list[str]:

    store = get_vector_store()
    texts = [chunk.page_content for chunk in chunks] 
    metadatas = [chunk.metadata for chunk in chunks] 

    print('texts:-----', len(texts))
    print('metadatas:-----', len(metadatas))

    ids = await store.aadd_texts(texts=texts, metadatas=metadatas) # 异步批量写入

    return ids  # 返回写入的id列表

async def delete_documents(qdrant_ids: list[str]):
    """删除文档数据"""

    # store = get_vector_store()
    # await store.delete(ids=qdrant_ids)

    client = get_qdrant_client()
    await client.delete(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        points=qdrant_ids,
    )



