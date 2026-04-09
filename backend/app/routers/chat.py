"""对话路由 - SSE 流式接口"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio

from app.models.schemas import ChatRequest, ChatStreamChunk, ReferenceChunk
from app.services.llm import get_llm_service
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口 - SSE"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            llm_service = get_llm_service()
            vector_store = get_vector_store()
            
            references = []
            
            # 1. 知识库检索
            if request.use_kb and request.kb_id:
                try:
                    results = await vector_store.search(
                        request.kb_id,
                        request.text,
                        request.top_k
                    )
                    
                    if results:
                        references = [
                            ReferenceChunk(
                                content=r["content"],
                                source=r["metadata"].get("filename", "未知"),
                                doc_id=r["metadata"].get("doc_id", ""),
                                similarity=r["similarity"]
                            )
                            for r in results
                        ]
                        
                        # 发送引用信息
                        ref_data = ChatStreamChunk(
                            type="reference",
                            references=references
                        ).model_dump()
                        yield f"event: reference\ndata: {json.dumps(ref_data, ensure_ascii=False)}\n\n"
                        
                except Exception as e:
                    # 检索失败，继续但不使用知识库
                    print(f"知识库检索失败: {e}")
            
            # 2. 构建 Prompt
            messages = llm_service.build_rag_prompt(
                code=request.code,
                query=request.text,
                references=[r.model_dump() for r in references],
                history=[{"role": m.role, "content": m.content} for m in request.messages]
            )
            
            # 3. 流式调用 LLM
            async for chunk in llm_service.stream_chat(messages):
                delta_data = ChatStreamChunk(
                    type="delta",
                    content=chunk
                ).model_dump()
                yield f"event: message\ndata: {json.dumps(delta_data, ensure_ascii=False)}\n\n"
            
            # 4. 发送完成信号
            done_data = ChatStreamChunk(type="done").model_dump()
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
            
        except Exception as e:
            error_data = ChatStreamChunk(
                type="error",
                error=str(e)
            ).model_dump()
            yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/test")
async def chat_test(request: ChatRequest):
    """非流式对话接口 - 测试用"""
    llm_service = get_llm_service()
    vector_store = get_vector_store()
    
    references = []
    
    # 知识库检索
    if request.use_kb and request.kb_id:
        results = await vector_store.search(
            request.kb_id,
            request.text,
            request.top_k
        )
        references = results
    
    # 构建提示
    messages = llm_service.build_rag_prompt(
        code=request.code,
        query=request.text,
        references=references,
        history=[{"role": m.role, "content": m.content} for m in request.messages]
    )
    
    # 调用 LLM
    response = await llm_service.chat(messages)
    
    return {
        "code": 0,
        "data": {
            "content": response,
            "references": references
        }
    }