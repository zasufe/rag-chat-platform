"""LLM 服务 - 支持流式输出"""
from typing import List, Dict, Any, AsyncGenerator, Optional
import httpx
import json
from app.core.config import settings


class LLMService:
    """LLM 调用服务"""
    
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.api_base = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        if not self.api_key:
            yield "错误：未配置 LLM API Key"
            return
        
        # 强制使用 IPv4，避免 IPv6 问题
        async with httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(max_connections=100)
        ) as client:
            try:
                print(f"LLM API 调用：{self.api_base}/chat/completions")
                print(f"Model: {self.model}")
                print(f"Messages: {len(messages)} 条")
                
                async with client.stream(
                    "POST",
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                        **kwargs
                    }
                ) as response:
                    print(f"LLM 响应状态码：{response.status_code}")
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"LLM 错误响应：{error_text}")
                        yield f"错误：API 调用失败 ({response.status_code}) {error_text.decode()[:200]}"
                        return
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and chunk["choices"]:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                                
            except Exception as e:
                yield f"错误：{str(e)}"
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """非流式对话"""
        if not self.api_key:
            return "错误：未配置 LLM API Key"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        **kwargs
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"错误：API 调用失败 ({response.status_code})"
                    
            except Exception as e:
                return f"错误：{str(e)}"
    
    def build_rag_prompt(
        self,
        code: str,
        query: str,
        references: List[Dict[str, Any]] = None,
        history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """构建 RAG 提示词 - 增强模式（知识库仅供参考，模型自由发挥）"""
        
        # 构建上下文
        context_text = ""
        if references:
            context_text = "\n\n".join([
                f"[参考文档 {i+1}] 来源：{ref.get('metadata', {}).get('filename', '未知')}\n{ref['content']}"
                for i, ref in enumerate(references)
            ])
        
        # 构建系统提示 - 增强模式
        if context_text:
            # 有知识库内容时：提供参考，但让模型自由决定是否使用
            system_prompt = f"""你是一个专业的 AI 助手。

## 参考资料（仅供参考）
以下资料**可能**与用户问题相关，你可以参考，但不必强制使用：

{context_text}

## 回答指南
1. **如果参考资料与问题相关**：结合资料内容，提供更准确、详细的回答
2. **如果参考资料与问题无关**：基于你的专业知识和能力，自由回答用户问题
3. **优先保证回答质量**：资料只是辅助，你的专业知识同样重要
4. **不必强制引用**：只有当资料确实有用时才参考，不需要时可以忽略
"""
        else:
            # 无知识库内容时：完全依赖模型自身能力
            system_prompt = """你是一个专业的 AI 助手，基于你的专业知识和能力回答用户问题。
"""
        
        # 添加代码上下文
        if code:
            system_prompt += f"""
## 当前页面代码上下文：
```
{code}
```
"""
        
        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史消息
        if history:
            messages.extend(history[-10:])  # 保留最近 10 条
        
        # 添加当前问题
        messages.append({"role": "user", "content": query})
        
        return messages


# 全局服务实例
llm_service = LLMService()


def get_llm_service() -> LLMService:
    """获取 LLM 服务实例"""
    return llm_service