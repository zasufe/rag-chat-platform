"""文档管理路由"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse
from typing import Optional
import uuid
import os
import json
from datetime import datetime
import aiofiles

from app.models.schemas import ApiResponse, DocumentListItem
from app.services.vector_store import get_vector_store
from app.services.document import get_document_service
from app.core.config import settings

router = APIRouter(prefix="/api/kb", tags=["文档管理"])

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


async def process_document_task(
    kb_id: str,
    doc_id: str,
    file_path: str,
    filename: str,
    chunk_size: int = 512,
    overlap: int = 100
):
    """后台任务：解析文档并入库"""
    document_service = get_document_service()
    vector_store = get_vector_store()
    
    try:
        # 1. 解析文档
        text = await document_service.parse_file(file_path)
        
        if not text:
            # 更新状态为失败
            metadata = await load_metadata()
            if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
                metadata[kb_id]["documents"][doc_id]["status"] = "failed"
                metadata[kb_id]["documents"][doc_id]["error_msg"] = "文档解析失败"
                await save_metadata(metadata)
            return
        
        # 2. 分块
        chunks = document_service.chunk_text(text, chunk_size, overlap)
        
        if not chunks:
            metadata = await load_metadata()
            if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
                metadata[kb_id]["documents"][doc_id]["status"] = "failed"
                metadata[kb_id]["documents"][doc_id]["error_msg"] = "文档分块失败"
                await save_metadata(metadata)
            return
        
        # 3. 向量化入库
        metadatas = [{"filename": filename} for _ in chunks]
        count = await vector_store.add_documents(kb_id, doc_id, chunks, metadatas)
        
        # 4. 更新元数据
        metadata = await load_metadata()
        if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
            metadata[kb_id]["documents"][doc_id]["status"] = "completed"
            metadata[kb_id]["documents"][doc_id]["chunks_count"] = count
            metadata[kb_id]["total_chunks"] = sum(
                doc.get("chunks_count", 0) 
                for doc in metadata[kb_id].get("documents", {}).values()
            )
            metadata[kb_id]["updated_at"] = datetime.now().isoformat()
            await save_metadata(metadata)
            
    except Exception as e:
        # 更新状态为失败
        print(f"文档处理失败: {e}")
        metadata = await load_metadata()
        if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
            metadata[kb_id]["documents"][doc_id]["status"] = "failed"
            metadata[kb_id]["documents"][doc_id]["error_msg"] = str(e)
            await save_metadata(metadata)


@router.post("/{kb_id}/docs/upload", response_model=ApiResponse)
async def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = Form(512),
    overlap: int = Form(100),
    description: Optional[str] = Form(None)
):
    """上传文档"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 验证文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    # 检查文件大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 生成文档 ID
    doc_id = str(uuid.uuid4())[:8]
    
    # 保存文件
    document_service = get_document_service()
    file_path = await document_service.save_file(kb_id, doc_id, file.filename, content)
    
    # 记录元数据
    if "documents" not in metadata[kb_id]:
        metadata[kb_id]["documents"] = {}
    
    metadata[kb_id]["documents"][doc_id] = {
        "doc_id": doc_id,
        "filename": file.filename,
        "file_size": len(content),
        "chunks_count": 0,
        "mime_type": document_service.get_mime_type(file.filename),
        "uploaded_at": datetime.now().isoformat(),
        "status": "processing",
        "description": description
    }
    metadata[kb_id]["updated_at"] = datetime.now().isoformat()
    await save_metadata(metadata)
    
    # 后台处理文档
    background_tasks.add_task(
        process_document_task,
        kb_id,
        doc_id,
        file_path,
        file.filename,
        chunk_size,
        overlap
    )
    
    return ApiResponse(
        code=0,
        message="文档上传成功，正在处理中",
        data={
            "doc_id": doc_id,
            "filename": file.filename,
            "chunks_count": 0,
            "file_size": len(content),
            "status": "processing"
        }
    )


@router.get("/{kb_id}/docs", response_model=ApiResponse)
async def list_documents(kb_id: str, page: int = 1, size: int = 20):
    """获取文档列表"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    documents = metadata[kb_id].get("documents", {})
    items = list(documents.values())
    
    # 分页
    total = len(items)
    start = (page - 1) * size
    end = start + size
    items = items[start:end]
    
    return ApiResponse(
        code=0,
        data={
            "total": total,
            "items": items
        }
    )


@router.delete("/{kb_id}/docs/{doc_id}", response_model=ApiResponse)
async def delete_document(kb_id: str, doc_id: str):
    """删除文档"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if doc_id not in metadata[kb_id].get("documents", {}):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = metadata[kb_id]["documents"][doc_id]
    
    # 删除向量库中的数据
    vector_store = get_vector_store()
    await vector_store.delete_document(kb_id, doc_id)
    
    # 删除本地文件
    document_service = get_document_service()
    await document_service.delete_file(kb_id, doc_id, doc_info["filename"])
    
    # 更新元数据
    del metadata[kb_id]["documents"][doc_id]
    metadata[kb_id]["updated_at"] = datetime.now().isoformat()
    await save_metadata(metadata)
    
    return ApiResponse(code=0, message="删除成功")


@router.get("/{kb_id}/docs/{doc_id}/download")
async def download_document(kb_id: str, doc_id: str):
    """下载原始文件"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if doc_id not in metadata[kb_id].get("documents", {}):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = metadata[kb_id]["documents"][doc_id]
    filename = doc_info["filename"]
    
    file_path = os.path.join(settings.STORAGE_DIR, kb_id, f"{doc_id}_{filename}")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        file_path,
        filename=filename,
        media_type=doc_info.get("mime_type", "application/octet-stream")
    )


@router.get("/{kb_id}/docs/{doc_id}/preview", response_model=ApiResponse)
async def preview_document(kb_id: str, doc_id: str):
    """预览文档"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if doc_id not in metadata[kb_id].get("documents", {}):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc_info = metadata[kb_id]["documents"][doc_id]
    filename = doc_info["filename"]
    mime_type = doc_info.get("mime_type", "")
    
    file_path = os.path.join(settings.STORAGE_DIR, kb_id, f"{doc_id}_{filename}")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 根据类型处理
    if mime_type == "application/pdf":
        # PDF 返回文件路径，前端用 iframe 展示
        return ApiResponse(
            code=0,
            data={
                "type": "pdf",
                "url": f"/api/kb/{kb_id}/docs/{doc_id}/download"
            }
        )
    else:
        # 其他类型提取文本预览
        document_service = get_document_service()
        text = await document_service.parse_file(file_path)
        
        # 截取前 5000 字符
        preview_text = text[:5000] if len(text) > 5000 else text
        
        return ApiResponse(
            code=0,
            data={
                "type": "text",
                "content": preview_text,
                "total_length": len(text)
            }
        )


@router.put("/{kb_id}/docs/{doc_id}", response_model=ApiResponse)
async def update_document(kb_id: str, doc_id: str, request: dict):
    """更新文档信息（描述）"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if doc_id not in metadata[kb_id].get("documents", {}):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 更新描述
    if "description" in request:
        metadata[kb_id]["documents"][doc_id]["description"] = request["description"]
        metadata[kb_id]["updated_at"] = datetime.now().isoformat()
        await save_metadata(metadata)
    
    return ApiResponse(code=0, message="更新成功")


@router.post("/{kb_id}/docs/{doc_id}/reupload", response_model=ApiResponse)
async def reupload_document(
    kb_id: str,
    doc_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: int = Form(512),
    overlap: int = Form(100),
    description: Optional[str] = Form(None)
):
    """重新上传文档"""
    metadata = await load_metadata()
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if doc_id not in metadata[kb_id].get("documents", {}):
        raise HTTPException(status_code=404, detail="文档不存在")
    
    old_doc = metadata[kb_id]["documents"][doc_id]
    
    # 验证文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    # 检查文件大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")
    
    # 删除旧的向量数据
    vector_store = get_vector_store()
    await vector_store.delete_document(kb_id, doc_id)
    
    # 删除旧文件
    document_service = get_document_service()
    old_file_path = os.path.join(settings.STORAGE_DIR, kb_id, f"{doc_id}_{old_doc['filename']}")
    if os.path.exists(old_file_path):
        os.remove(old_file_path)
    
    # 保存新文件
    file_path = await document_service.save_file(kb_id, doc_id, file.filename, content)
    
    # 更新元数据
    metadata[kb_id]["documents"][doc_id] = {
        "doc_id": doc_id,
        "filename": file.filename,
        "file_size": len(content),
        "chunks_count": 0,
        "mime_type": document_service.get_mime_type(file.filename),
        "uploaded_at": datetime.now().isoformat(),
        "status": "processing",
        "description": description or old_doc.get("description")
    }
    metadata[kb_id]["updated_at"] = datetime.now().isoformat()
    await save_metadata(metadata)
    
    # 后台处理文档
    background_tasks.add_task(
        process_document_task,
        kb_id,
        doc_id,
        file_path,
        file.filename,
        chunk_size,
        overlap
    )
    
    return ApiResponse(
        code=0,
        message="重新上传成功，正在处理中",
        data={
            "doc_id": doc_id,
            "filename": file.filename,
            "status": "processing"
        }
    )