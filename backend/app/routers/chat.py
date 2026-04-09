"""对话路由 - SSE 流式接口"""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime

from app.models.schemas import ChatRequest, ChatStreamChunk, ReferenceChunk
from app.services.llm import get_llm_service
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式对话接口 - SSE"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            print(f"\n{'='*60}")
            print(f"收到对话请求:")
            print(f"  - 问题：{request.text[:50]}...")
            print(f"  - 使用知识库：{request.use_kb}")
            print(f"  - 知识库 ID: {request.kb_id}")
            print(f"  - Top-K: {request.top_k}")
            print(f"{'='*60}\n")
            
            llm_service = get_llm_service()
            vector_store = get_vector_store()
            
            references = []
            
            # 1. 知识库检索
            if request.use_kb and request.kb_id:
                print(f"📚 开始知识库检索...")
                try:
                    results = await vector_store.search(
                        request.kb_id,
                        request.text,
                        request.top_k
                    )
                    
                    print(f"  ✓ 检索到 {len(results)} 条结果")
                    
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
                        print(f"  ✓ 发送引用信息")
                        yield f"event: reference\ndata: {json.dumps(ref_data, ensure_ascii=False)}\n\n"
                        
                except Exception as e:
                    # 检索失败，继续但不使用知识库
                    print(f"  ✗ 知识库检索失败：{e}")
            else:
                print(f"  ⚠ 不使用知识库")
            
            # 2. 构建 Prompt
            print(f"\n🔨 构建 Prompt...")
            messages = llm_service.build_rag_prompt(
                code=request.code,
                query=request.text,
                references=[r.model_dump() for r in references],
                history=[{"role": m.role, "content": m.content} for m in request.messages]
            )
            
            print(f"  ✓ Prompt 构建完成：{len(messages)} 条消息")
            for i, msg in enumerate(messages):
                content_preview = msg['content'][:80].replace('\n', ' ')
                print(f"    [{i}] {msg['role']}: {content_preview}...")
            
            # 3. 流式调用 LLM
            print(f"\n🤖 调用 LLM...")
            llm_start_time = datetime.now()
            content_length = 0
            
            try:
                async for chunk in llm_service.stream_chat(messages):
                    delta_data = ChatStreamChunk(
                        type="delta",
                        content=chunk
                    ).model_dump()
                    content_length += len(chunk)
                    yield f"event: message\ndata: {json.dumps(delta_data, ensure_ascii=False)}\n\n"
                
                llm_end_time = datetime.now()
                llm_duration = (llm_end_time - llm_start_time).total_seconds()
                print(f"  ✓ LLM 调用完成：{content_length} 字符，耗时 {llm_duration:.2f}秒")
            except Exception as llm_error:
                print(f"  ✗ LLM 调用失败：{llm_error}")
                raise
            
            # 4. 发送完成信号
            done_data = ChatStreamChunk(type="done").model_dump()
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
            
            print(f"\n{'='*60}")
            print(f"对话完成 ✓")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"对话失败 ✗")
            print(f"错误：{e}")
            print(f"{'='*60}\n")
            
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
