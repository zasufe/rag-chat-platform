"""向量存储服务 - ChromaDB PersistentClient"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import os
import json
import uuid
from datetime import datetime
import aiofiles
import asyncio

from app.core.config import settings


class VectorStoreService:
    """向量存储服务"""
    
    def __init__(self):
        self.client: Optional[chromadb.Client] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化 ChromaDB 客户端"""
        if self._initialized:
            return
        
        # 确保目录存在
        os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        
        # 创建 PersistentClient
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self._initialized = True
    
    async def create_collection(self, kb_id: str) -> bool:
        """创建知识库 Collection"""
        await self.initialize()
        
        try:
            self.client.create_collection(
                name=f"kb_{kb_id}",
                metadata={"created_at": datetime.now().isoformat()}
            )
            return True
        except Exception as e:
            print(f"创建 Collection 失败: {e}")
            return False
    
    async def delete_collection(self, kb_id: str) -> bool:
        """删除知识库 Collection"""
        await self.initialize()
        
        try:
            self.client.delete_collection(name=f"kb_{kb_id}")
            return True
        except Exception as e:
            print(f"删除 Collection 失败: {e}")
            return False
    
    async def add_documents(
        self,
        kb_id: str,
        doc_id: str,
        chunks: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> int:
        """添加文档块到向量库"""
        await self.initialize()
        
        try:
            collection = self.client.get_collection(name=f"kb_{kb_id}")
            
            # 生成 ID
            ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
            
            # 准备元数据
            if metadatas is None:
                metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]
            else:
                for i, meta in enumerate(metadatas):
                    meta["doc_id"] = doc_id
                    meta["chunk_index"] = i
            
            # ChromaDB 会自动生成 embeddings
            collection.add(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            
            return len(chunks)
        except Exception as e:
            print(f"添加文档失败: {e}")
            return 0
    
    async def delete_document(self, kb_id: str, doc_id: str) -> bool:
        """删除指定文档的所有块"""
        await self.initialize()
        
        try:
            collection = self.client.get_collection(name=f"kb_{kb_id}")
            
            # 查询该文档的所有 ID
            results = collection.get(
                where={"doc_id": doc_id}
            )
            
            if results["ids"]:
                collection.delete(ids=results["ids"])
            
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    async def search(
        self,
        kb_id: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """向量检索"""
        await self.initialize()
        
        try:
            collection = self.client.get_collection(name=f"kb_{kb_id}")
            
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            formatted = []
            if results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i] if results["distances"] else 0
                    # ChromaDB 余弦距离范围 [0, 2]，转换为相似度 [-1, 1]
                    similarity = 1 - distance
                    # 如果相似度为负，说明距离>1，使用原始距离的相反数
                    if similarity < 0:
                        similarity = -distance
                    
                    formatted.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "similarity": similarity
                    })
            
            return formatted
        except Exception as e:
            print(f"检索失败: {e}")
            return []
    
    async def get_collection_count(self, kb_id: str) -> int:
        """获取 Collection 文档数"""
        await self.initialize()
        
        try:
            collection = self.client.get_collection(name=f"kb_{kb_id}")
            return collection.count()
        except:
            return 0
    
    async def list_collections(self) -> List[str]:
        """列出所有 Collection"""
        await self.initialize()
        
        collections = self.client.list_collections()
        return [c.name for c in collections]


# 全局服务实例
vector_store = VectorStoreService()


def get_vector_store() -> VectorStoreService:
    """获取向量存储服务实例"""
    return vector_store