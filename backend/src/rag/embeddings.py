from langchain_huggingface import HuggingFaceEmbeddings

# 缓存嵌入模型 避免重复加载
from functools import lru_cache

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
#全局缓存 只加载一次模型
@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:


    return HuggingFaceEmbeddings(
        model_name = "BAAI/bge-base-zh", # 嵌入模型BAAI/bge-base-zh  中文优化的轻量嵌入模型
        model_kwargs = {"device": "cpu"}, # 模型运行在CPU上 兼容没有GPU的环境
        encode_kwargs = {"normalize_embeddings": True} # 对嵌入向量进行归一化
        )