from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# APP_DIR : 应用目录
# SRC_DIR = Path(__file__).resolve().parent

# ROOT_DIR : 项目根目录
# ROOT_DIR = SRC_DIR.parent

#继承BaseSettings类 ： 自动从环境变量文件中读取配置项
class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",  # 环境变量文件路径
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 之前配置
    # class Config:
    #     # 配置环境变量文件路径
    #     env_file = ROOT_DIR / ".env"
    #     env_file_encoding = "utf-8"

    APP_NAME: str = "Campus RAG System"  # 应用名称 默认值
    DEBUG: bool = True


    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "campus_rag_2412"

    #动态属性
    @property
    def DATABASE_URL(self) -> str:
        """动态构建数据库连接 URL"""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
   
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "campus_knowledge_2412"
    QDRANT_VECTOR_SIZE: int = 768 # bge_base_zh


    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    DEEPSEEK_API_KEY: str = ""  # 从环境变量或 .env 读取，切勿在此硬编码真实密钥
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-v4-flash"


    CHUNK_SIZE: int = 500 
    CHUNK_OVERLAP: int = 50
    RETRIEVER_TOP_K: int = 3
    SHOW_SOURCE: bool = True


    DATA_DIR: str = "data"

settings = Settings() # 实例化配置类 全局唯一实例