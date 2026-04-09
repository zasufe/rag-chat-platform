"""Pydantic 数据模型定义"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============ 消息相关模型 ============

class Message(BaseModel):
    """对话消息"""
    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: Optional[datetime] = None


class ReferenceChunk(BaseModel):
    """引用文档块"""
    content: str
    source: str  # 原始文件名
    doc_id: str
    similarity: float


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[Message] = Field(default_factory=list)
    code: str = Field(default="", description="当前页面代码上下文")
    text: str = Field(..., description="用户当前问题")
    kb_id: Optional[str] = Field(None, description="知识库ID")
    use_kb: bool = Field(True, description="是否使用知识库")
    top_k: int = Field(3, ge=1, le=10, description="检索数量")


class ChatStreamChunk(BaseModel):
    """SSE 流式响应数据格式"""
    type: Literal["delta", "done", "error", "reference"]
    content: Optional[str] = None
    references: Optional[List[ReferenceChunk]] = None
    error: Optional[str] = None


# ============ 知识库相关模型 ============

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=100)


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: str = Field(..., min_length=1, max_length=100)


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: str
    name: str
    document_count: int = 0
    total_chunks: int = 0
    created_at: datetime
    updated_at: datetime


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    items: List[KnowledgeBaseResponse]
    total: int


# ============ 文档相关模型 ============

class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    code: int = 0
    data: dict


class DocumentListItem(BaseModel):
    """文档列表项"""
    doc_id: str
    filename: str
    file_size: int
    chunks_count: int = 0
    mime_type: str
    uploaded_at: datetime
    status: Literal["processing", "completed", "failed"]
    error_msg: Optional[str] = None
    description: Optional[str] = None  # 文件描述


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    code: int = 0
    data: dict


# ============ 检索相关模型 ============

class SearchQuery(BaseModel):
    """检索查询请求"""
    query: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=10)


class SearchResult(BaseModel):
    """检索结果"""
    chunks: List[ReferenceChunk]


# ============ 通用响应模型 ============

class ApiResponse(BaseModel):
    """通用 API 响应"""
    code: int = 0
    message: str = "success"
    data: Optional[dict] = None