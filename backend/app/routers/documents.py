"""文档管理路由"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import FileResponse
from typing import Optional
import uuid
import os
from datetime import datetime

from app.models.schemas import ApiResponse
from app.services.vector_store import get_vector_store
from app.services.document import get_document_service
from app.core.config import settings
from app.services.metadata_store import MetadataStoreError, metadata_store

router = APIRouter(prefix="/api/kb", tags=["文档管理"])


def raise_metadata_error(e: MetadataStoreError):
    raise HTTPException(status_code=500, detail=str(e)) from e


async def mark_document_failed(kb_id: str, doc_id: str, error_msg: str):
    """后台任务失败时更新文档状态。"""
    try:
        def update_status(metadata: dict):
            if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
                metadata[kb_id]["documents"][doc_id]["status"] = "failed"
                metadata[kb_id]["documents"][doc_id]["error_msg"] = error_msg
                metadata[kb_id]["updated_at"] = datetime.now().isoformat()

        await metadata_store.update(update_status)
    except MetadataStoreError as e:
        print(f"更新文档失败状态失败: {e}")


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
            await mark_document_failed(kb_id, doc_id, "文档解析失败")
            return
        
        # 2. 分块
        chunks = document_service.chunk_text(text, chunk_size, overlap)
        
        if not chunks:
            await mark_document_failed(kb_id, doc_id, "文档分块失败")
            return
        
        # 3. 向量化入库
        metadatas = [{"filename": filename} for _ in chunks]
        count = await vector_store.add_documents(kb_id, doc_id, chunks, metadatas)
        
        # 4. 更新元数据
        def complete_document(metadata: dict):
            if kb_id in metadata and doc_id in metadata[kb_id].get("documents", {}):
                metadata[kb_id]["documents"][doc_id]["status"] = "completed"
                metadata[kb_id]["documents"][doc_id]["chunks_count"] = count
                metadata[kb_id]["total_chunks"] = sum(
                    doc.get("chunks_count", 0)
                    for doc in metadata[kb_id].get("documents", {}).values()
                )
                metadata[kb_id]["updated_at"] = datetime.now().isoformat()

        await metadata_store.update(complete_document)
            
    except Exception as e:
        print(f"文档处理失败: {e}")
        await mark_document_failed(kb_id, doc_id, str(e))


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
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)

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
    
    try:
        def add_document(metadata: dict):
            if kb_id not in metadata:
                raise HTTPException(status_code=404, detail="知识库不存在")
            metadata[kb_id].setdefault("documents", {})
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

        await metadata_store.update(add_document)
    except MetadataStoreError as e:
        await document_service.delete_file(kb_id, doc_id, file.filename)
        raise_metadata_error(e)
    except HTTPException:
        await document_service.delete_file(kb_id, doc_id, file.filename)
        raise
    
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
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
    if kb_id not in metadata:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    documents = metadata[kb_id].get("documents", {})
    items = list(documents.values())
    items.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)
    
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
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
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
    
    try:
        def remove_document(current_metadata: dict):
            if kb_id not in current_metadata:
                raise HTTPException(status_code=404, detail="知识库不存在")
            if doc_id not in current_metadata[kb_id].get("documents", {}):
                raise HTTPException(status_code=404, detail="文档不存在")
            del current_metadata[kb_id]["documents"][doc_id]
            current_metadata[kb_id]["updated_at"] = datetime.now().isoformat()

        await metadata_store.update(remove_document)
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
    return ApiResponse(code=0, message="删除成功")


@router.get("/{kb_id}/docs/{doc_id}/download")
async def download_document(kb_id: str, doc_id: str):
    """下载原始文件"""
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
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
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
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
    try:
        def update_description(metadata: dict):
            if kb_id not in metadata:
                raise HTTPException(status_code=404, detail="知识库不存在")
            if doc_id not in metadata[kb_id].get("documents", {}):
                raise HTTPException(status_code=404, detail="文档不存在")
            if "description" in request:
                metadata[kb_id]["documents"][doc_id]["description"] = request["description"]
                metadata[kb_id]["updated_at"] = datetime.now().isoformat()

        await metadata_store.update(update_description)
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
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
    try:
        metadata = await metadata_store.load()
    except MetadataStoreError as e:
        raise_metadata_error(e)
    
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
    
    try:
        def replace_document(metadata: dict):
            if kb_id not in metadata:
                raise HTTPException(status_code=404, detail="知识库不存在")
            if doc_id not in metadata[kb_id].get("documents", {}):
                raise HTTPException(status_code=404, detail="文档不存在")
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

        await metadata_store.update(replace_document)
    except MetadataStoreError as e:
        await document_service.delete_file(kb_id, doc_id, file.filename)
        raise_metadata_error(e)
    except HTTPException:
        await document_service.delete_file(kb_id, doc_id, file.filename)
        raise
    
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
