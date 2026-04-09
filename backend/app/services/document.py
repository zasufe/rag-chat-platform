"""文档处理服务 - 解析、分块"""
from typing import List, Optional
import os
import uuid
import aiofiles
from datetime import datetime
import re

from app.core.config import settings


class DocumentService:
    """文档处理服务"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.storage_dir = settings.STORAGE_DIR
    
    async def save_file(
        self,
        kb_id: str,
        doc_id: str,
        filename: str,
        content: bytes
    ) -> str:
        """保存文件到本地"""
        # 创建目录
        dir_path = os.path.join(self.storage_dir, kb_id)
        os.makedirs(dir_path, exist_ok=True)
        
        # 生成文件路径
        file_path = os.path.join(dir_path, f"{doc_id}_{filename}")
        
        # 保存文件
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return file_path
    
    async def parse_file(self, file_path: str) -> str:
        """解析文件，提取文本"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext == ".pdf":
                return await self._parse_pdf(file_path)
            elif ext in [".docx", ".doc"]:
                return await self._parse_docx(file_path)
            elif ext in [".txt", ".md"]:
                return await self._parse_text(file_path)
            else:
                return ""
        except Exception as e:
            print(f"解析文件失败: {e}")
            return ""
    
    async def _parse_pdf(self, file_path: str) -> str:
        """解析 PDF 文件"""
        from PyPDF2 import PdfReader
        
        text_parts = []
        try:
            # 同步操作需要在线程中执行
            import asyncio
            loop = asyncio.get_event_loop()
            
            def read_pdf():
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
            
            return await loop.run_in_executor(None, read_pdf)
        except Exception as e:
            print(f"PDF 解析错误: {e}")
            return ""
    
    async def _parse_docx(self, file_path: str) -> str:
        """解析 Word 文件"""
        from docx import Document
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            def read_docx():
                doc = Document(file_path)
                paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                return "\n".join(paragraphs)
            
            return await loop.run_in_executor(None, read_docx)
        except Exception as e:
            print(f"Word 解析错误: {e}")
            return ""
    
    async def _parse_text(self, file_path: str) -> str:
        """解析文本文件"""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                return await f.read()
        except UnicodeDecodeError:
            try:
                async with aiofiles.open(file_path, "r", encoding="gbk") as f:
                    return await f.read()
            except:
                return ""
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """递归字符分块"""
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        if not text:
            return []
        
        # 清理文本
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            # 尝试在句子边界处分块
            chunk = text[start:end]
            
            # 查找最后一个句号、问号、感叹号
            last_punct = max(
                chunk.rfind("。"),
                chunk.rfind("！"),
                chunk.rfind("？"),
                chunk.rfind("."),
                chunk.rfind("!"),
                chunk.rfind("?"),
                chunk.rfind("\n")
            )
            
            if last_punct > chunk_size * 0.3:
                end = start + last_punct + 1
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    def get_mime_type(self, filename: str) -> str:
        """获取文件 MIME 类型"""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown"
        }
        return mime_types.get(ext, "application/octet-stream")
    
    async def delete_file(self, kb_id: str, doc_id: str, filename: str) -> bool:
        """删除文件"""
        try:
            file_path = os.path.join(self.storage_dir, kb_id, f"{doc_id}_{filename}")
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    async def delete_kb_files(self, kb_id: str) -> bool:
        """删除知识库所有文件"""
        try:
            import shutil
            dir_path = os.path.join(self.storage_dir, kb_id)
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
            return True
        except Exception as e:
            print(f"删除知识库文件失败: {e}")
            return False


# 全局服务实例
document_service = DocumentService()


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    return document_service