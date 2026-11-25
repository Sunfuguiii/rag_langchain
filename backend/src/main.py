from fastapi import FastAPI
from src.db.engine import init_db, close_db
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from src.api.auth import router as auth_router
from src.api.document import router as document_router
from src.api.chat import router as chat_router

import os
# 限制矩阵运算线程，解决OpenBLAS内存报错
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # startup
    try:
        await init_db()
        print("[OK] Database connected successfully")
    except Exception as e:
        print(f"[WARN] Database connection failed: {e}")
        print("   Server started, but database is unavailable. Run: uv run python -m scripts.init_db")
    yield
    # shutdown
    await close_db()



app = FastAPI(
    lifespan=lifespan,
)


# cors 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(document_router, prefix="/api/v1/documents", tags=["文档管理"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["问答"])



@app.get("/")
def read_root():
    return {"Hello": "World"}


# uv run uvicorn src.main:app --workers 1 --reload --port 8000
# uv run uvicorn src.main:app --reload --port 8000