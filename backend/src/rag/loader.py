from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from src.config import settings 

def load_and_split_document(file_path: str) -> list:
    
    headers_to_split_on = [
        ("##", "chapter"),   # 二级标题 → metadata["chapter"]
        ("###", "section"),  # 三级标题 → metadata["section"]
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
    )

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 粗切
    md_docs = markdown_splitter.split_text(content)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        # 自定义分隔符 
        # 优先级：\n\n > \n > "。" > ! > ? > ; > space > empty string
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )

    chunks = text_splitter.split_documents(md_docs)

    for chunk in chunks:
        chunk.metadata.setdefault("source", file_path)
    
    return chunks
