# RAG Chat Platform - 智能对话平台

基于 LangChain + FastAPI + Vue3 的 RAG 对话系统，支持知识库增强和流式对话。

## 🚀 快速启动

### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（已配置好 Qwen API）
# 编辑 .env 文件

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 访问地址

- **前端界面**: http://172.16.25.187:3000
- **API 文档**: http://172.16.25.187:8000/docs
- **健康检查**: http://172.16.25.187:8000/health

---

## 📁 项目结构

```
rag-chat-platform/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py            # FastAPI 主应用
│   │   ├── core/
│   │   │   └── config.py      # 配置管理
│   │   ├── models/
│   │   │   └── schemas.py     # Pydantic 模型
│   │   ├── routers/
│   │   │   ├── chat.py        # 对话路由（SSE 流式）
│   │   │   ├── knowledge_base.py  # 知识库 CRUD
│   │   │   └── documents.py   # 文档管理
│   │   └── services/
│   │       ├── vector_store.py    # ChromaDB 服务
│   │       ├── llm.py         # LLM 调用服务
│   │       └── document.py    # 文档解析服务
│   ├── storage/               # 文件存储
│   ├── requirements.txt
│   └── .env
│
└── frontend/                   # 前端应用
    ├── src/
    │   ├── main.ts            # 入口文件
    │   ├── App.vue            # 根组件
    │   ├── router/            # 路由配置
    │   ├── stores/            # Pinia 状态管理
    │   ├── composables/       # 组合式函数
    │   ├── types/             # TypeScript 类型
    │   └── views/             # 页面组件
    │       ├── ChatView.vue   # 对话页面
    │       └── KnowledgeBase/ # 知识库管理
    ├── package.json
    └── vite.config.ts
```

---

## 🔧 核心功能

### 1. 流式对话 (SSE)

- 实时打字机效果
- 支持中断生成
- Markdown 渲染
- 代码高亮

### 2. 知识库管理

- 创建/删除知识库
- 文档上传（PDF/Word/TXT）
- 自动分块和向量化
- 检索测试

### 3. RAG 增强

- 知识库检索增强
- 引用溯源展示
- 相似度评分

---

## 📡 API 接口

### 对话接口

```
POST /api/chat/stream
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "问题"}],
  "code": "",
  "text": "当前问题",
  "kb_id": "知识库ID",
  "use_kb": true,
  "top_k": 3
}

Response: text/event-stream (SSE)
```

### 知识库接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/kb | 创建知识库 |
| GET | /api/kb | 列表 |
| DELETE | /api/kb/{id} | 删除 |
| POST | /api/kb/{id}/search | 检索 |

### 文档接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/kb/{id}/docs/upload | 上传文档 |
| GET | /api/kb/{id}/docs | 文档列表 |
| GET | /api/kb/{id}/docs/{doc_id}/download | 下载 |
| DELETE | /api/kb/{id}/docs/{doc_id} | 删除 |

---

## ⚙️ 配置说明

### 后端环境变量 (.env)

```bash
# LLM 配置
LLM_API_KEY=your_api_key
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen3.5-flash

# 分块配置
CHUNK_SIZE=512
CHUNK_OVERLAP=100
```

### 前端配置 (vite.config.ts)

```typescript
server: {
  host: '0.0.0.0',
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://172.16.25.187:8000',
      changeOrigin: true
    }
  }
}
```

---

## 🔐 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 向量数据库 | ChromaDB |
| 文档解析 | PyPDF2 + python-docx |
| 前端框架 | Vue 3 + TypeScript |
| UI 组件 | Element Plus |
| 状态管理 | Pinia |
| 构建工具 | Vite |

---

**版本**: 2.0.0  
**更新日期**: 2026-04-08