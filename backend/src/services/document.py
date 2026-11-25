from langchain_qdrant import qdrant

from src.db.models import Chunk, Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pathlib import Path
from src.config import settings
import uuid
from src.rag.loader import load_and_split_document
from src.rag.vector_store import index_documents, delete_documents
import os



async def list_documents(db: AsyncSession) -> list[Document]:
      """获取所有文档"""
      result = await db.execute(
            select(Document).order_by(Document.created_at.desc()) # 按创建时间降序排序,desc() 表示降序排序
      )

      return list(result.scalars().all())

async def upload_document(
    filename: str, 
    content: bytes,
    user_id: str,
    db: AsyncSession,
) -> Document:
      """上传文档
        1. 保存文档到本地磁盘
        2. 保存文档元数据到postgresql数据库(indexing)
        3. 文档分割为多个chunk
        4. 保存chunk到qdrant数据库
        5. chunk元数据 保存到postgresql 数据库
        6. 更新文档状态为 ready 和 chunk_count

        异常处理：
           更新文档状态为 error 

        返回：
          文档对象（已经持久化（data + postgresql） + 向量化）
      
      """

    #   保存文件到本地磁盘
      data_dir = Path(settings.DATA_DIR)
      data_dir.mkdir(exist_ok=True)
      file_path = data_dir / f"{uuid.uuid4()}_{filename}"
      file_path.write_bytes(content)

    #   保存文档元数据到postgresql数据库(pedding)
      document = Document(
        user_id=user_id,
        filename=filename, # abc.md
        title= Path(filename).stem, # abc
        file_path=str(file_path),
        file_size=len(content),
        status="indexing"
      )
      db.add(document)
      await db.flush()

      try:

        # 文档分割为多个chunk
        chunks = load_and_split_document(str(file_path))
        print('chunks:-----', len(chunks))

        #   保存chunk到qdrant数据库
        qdrant_ids = await index_documents(chunks)

        print('qdrant_ids:-----', qdrant_ids)


        #   保存chunk元数据到postgresql 数据库
        for i, (chunk, qdrant_id) in enumerate(zip(chunks, qdrant_ids)):
                chunk_pg = Chunk(
                    document_id=document.id,
                    content=chunk.page_content,
                    chunk_index=i,
                    extra_meta=chunk.metadata,
                    qdrant_id=qdrant_id
                )
                db.add(chunk_pg)
        await db.commit()

        #   更新文档状态为 ready 和 chunk_count
        document.status = "ready"
        document.chunk_count = len(chunks)
        await db.commit()
      except Exception as e:
        document.status = "error"
        await db.commit()
        raise e
      
      return document

async def delete_document(doc_id: str, db: AsyncSession):
      """删除文档
      # 2. 从qdrant数据库删除文档
      # 3. 从本地磁盘删除文档
      # 4. 从postgresql数据库删除文档
      
      """
      result = await db.execute(
            select(Document).where(Document.id == doc_id)
      )

      doc = result.scalar_one_or_none()
      if doc is None:
        return 
      
      # 从qdrant数据库删除文档
      # 直接删除文档集合 了解

      #直接删除集合对应的所有数据点
      chunk_result = await db.execute(
          select(Chunk.qdrant_id).where(Chunk.document_id == doc.id)
      )

      print('chunk_result:-----', chunk_result)
      print('chunk_count:-----', chunk_result.scalars().all())

      qdrant_ids = chunk_result.scalars().all()
      if qdrant_ids:
        await delete_documents(qdrant_ids)

      # 从本地磁盘删除文档
      if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

      # 从postgresql数据库删除文档
      await db.delete(doc)
      await db.commit()
    