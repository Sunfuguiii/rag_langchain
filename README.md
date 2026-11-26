# 校园智能问答系统 · Campus RAG System

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-DC244C?style=flat-square&logo=qdrant&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)

基于 RAG（检索增强生成）的校园文档智能问答系统：上传校园文档 → 向量化入库 → 检索相关知识 → 大模型流式生成回答，支持来源追溯。

## ✨ 功能特性

- 🔐 **用户认证** — JWT 登录/注册，bcrypt 密码哈希
- 📄 **文档管理** — 上传、分块、向量化入库（Qdrant）
- 🤖 **智能问答** — 基于检索结果的 RAG 问答，SSE 流式输出
- 🔍 **来源追溯** — 回答附带引用来源文档
- 🧩 **MCP Server** — 提供 MCP 协议接口，可被 Claude 等客户端调用
- 🎨 **主题切换** — 明暗主题（next-themes）

## 🛠 技术栈

| 层 | 技术选型 |
|---|---|
| 后端框架 | FastAPI（async） |
| RAG 框架 | LangChain 1.3 |
| 向量数据库 | Qdrant |
| Embedding | sentence-transformers（BGE 中文，768 维） |
| LLM | DeepSeek / Ollama（可切换） |
| 流式输出 | SSE（sse-starlette） |
| 数据库 | PostgreSQL（asyncpg） |
| 协议 | MCP（Model Context Protocol） |
| 认证 | JWT（python-jose）+ bcrypt |
| 前端 | Next.js 16 · React 19 · TypeScript |
| UI | Tailwind CSS v4 · shadcn/ui · TanStack Query |

## 📁 项目结构

```
.
├── backend/                    # FastAPI 后端
│   ├── src/
│   │   ├── api/                # 路由：auth / document / chat
│   │   ├── rag/                # RAG 链路：loader / embeddings / vector_store / chain
│   │   ├── services/           # 业务服务：chat / document
│   │   ├── db/                 # 数据库引擎与 ORM 模型
│   │   ├── core/               # 依赖注入 / 安全
│   │   ├── schemas/            # Pydantic 模型
│   │   └── main.py             # 应用入口
│   ├── scripts/init_db.py      # 数据库初始化脚本
│   └── mcp_server.py           # MCP Server
└── frontend/                   # Next.js 前端
    └── src/
        ├── app/                # 页面路由（chat / documents / login / register）
        ├── components/         # UI 组件
        └── lib/                # API 封装
```

## 🚀 快速启动

### 后端

```bash
cd backend
cp .env.example .env            # 配置环境变量
uv sync                         # 安装依赖
uv run python -m scripts.init_db   # 初始化数据库
uv run uvicorn src.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
pnpm install
pnpm dev
```

浏览器访问 http://localhost:3000

## ⚙️ 环境变量

在 `backend/.env` 中配置（模板见 `backend/.env.example`）：

```ini
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=campus_rag_system

# Qdrant 向量库
QDRANT_HOST=localhost
QDRANT_PORT=6333

# LLM（ollama | deepseek）
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

## 📌 核心设计

- **RAG 链路**：文档加载 → 文本分块（chunk）→ BGE 向量化 → Qdrant 入库 → 相似度检索 → LLM 生成
- **多 Provider 支持**：LLM 可在 Ollama（本地）/ DeepSeek（云端）间切换，体现模型无关设计
- **流式体验**：SSE 流式输出，前端逐字渲染
- **来源可追溯**：回答附带来源文档片段

## 📄 License

MIT
