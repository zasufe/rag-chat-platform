"""知识库管理路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import uuid
import os
import json
from datetime import datetime
import aiofiles

from app.models.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    ApiResponse
)
from app.services.vector_store import get_vector_store
from app.services.document import get_document_service
from app.core.config import settings

router = APIRouter(prefix="/api/kb", tags=["知识库管理"])

# 元数据存储路径
METADATA_FILE = os.path.join(settings.STORAGE_DIR, "kb_metadata.json")


async def load_metadata() -> dict:
    """加载元数据"""
    if os.path.exists(METADATA_FILE):
        try:
            async with aiofiles.open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.loads(await f.read())
        except:
            return {}
    return {}


async def save_metadata(data: dict):
    """保存元数据"""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    async with aiofiles.open(METADATA_FILE, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


@router.post("", response_model=ApiResponse)
async def create_knowledge_base(request: KnowledgeBaseCreate):
    """创建知识库"""
    kb_id = str(uuid.uuid4())
    vector_store = get_vector_store()
    
    # 创建 ChromaDB Collection
    success = await vector_store.create_collection(kb_id)
    if not success:
        raise HTTPException(status_code=500, detail="创建向量库失败")
    
    # 保存元数据
    metadata = await load_metadata()
    metadata[kb_id] = {
        "id": kb_id,
        "name": request.name,
        "document_count": 0,
        "total_chunks": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "documents": {}
    }
    await save_metadata(metadata)
    
    return ApiResponse(
        code=0,
        message="创建成功",
        data={"kb_id": kb_id, "name": request.name}
    )


@router.get("", response_model=KnowledgeBaseListResponse)
async def list_knowledge_bases():
    """获取知识库列表"""
    metadata = await load_metadata()
    vector_store = get_vector_store()
    
    items = []
    for kb_id, kb_data in metadata.items():
        # 获取实际的文档数
        total_chunks = await vector_store.get_collection_count(kb_id)
        
        items.append(KnowledgeBaseResponse(
            id=kb_id,
            name=kb_data.get("name", "未命名"),
            document_count=len(kb_data.get("documents", {})),
            total_chunks=total_chunks,
            created_at=datetime.fromisoformat(kb_data["created_at"]),
            updated_at=datetime.fromisoformat(kb_data["updated_at"])
        ))
    
    return KnowledgeBaseListResponse(items=items, total=len(items))


@router.get("/{kb_id}", response_model=ApiResponse)
async def get_knowledge_base(kb_id: str):
    """获取知识库详情"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    kb_data = metadata[kb_id]
    vector_store = get_vector_store()
    total_chunks = await vector_store.get_collection_count(kb_id)
    
    return ApiResponse(
        code=0,
        data={
            "id": kb_id,
            "name": kb_data.get("name", "未命名"),
            "document_count": len(kb_data.get("documents", {})),
            "total_chunks": total_chunks,
            "created_at": kb_data["created_at"],
            "updated_at": kb_data["updated_at"]
        }
    )


@router.put("/{kb_id}", response_model=ApiResponse)
async def update_knowledge_base(kb_id: str, request: KnowledgeBaseUpdate):
    """更新知识库"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    metadata[kb_id]["name"] = request.name
    metadata[kb_id]["updated_at"] = datetime.now().isoformat()
    await save_metadata(metadata)
    
    return ApiResponse(code=0, message="更新成功")


@router.delete("/{kb_id}", response_model=ApiResponse)
async def delete_knowledge_base(kb_id: str):
    """删除知识库（级联删除）"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    vector_store = get_vector_store()
    document_service = get_document_service()
    
    # 删除 Collection
    await vector_store.delete_collection(kb_id)
    
    # 删除本地文件
    await document_service.delete_kb_files(kb_id)
    
    # 删除元数据
    del metadata[kb_id]
    await save_metadata(metadata)
    
    return ApiResponse(code=0, message="删除成功")


@router.post("/{kb_id}/search", response_model=ApiResponse)
async def search_knowledge_base(kb_id: str, query: dict):
    """知识库检索"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    vector_store = get_vector_store()
    
    query_text = query.get("query", "")
    top_k = query.get("top_k", 3)
    
    if not query_text:
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    
    results = await vector_store.search(kb_id, query_text, top_k)
    
    # 格式化结果
    chunks = [
        {
            "content": r["content"],
            "source": r["metadata"].get("filename", "未知"),
            "doc_id": r["metadata"].get("doc_id", ""),
            "similarity": round(r["similarity"], 4)
        }
        for r in results
    ]
    
    return ApiResponse(code=0, data={"chunks": chunks})