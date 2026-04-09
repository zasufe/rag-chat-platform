"""配置管理模块"""
import os
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

# 获取项目根目录（backend 的父目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 获取 backend 目录（.env 所在目录）
BACKEND_DIR = os.path.dirname(BASE_DIR)


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "RAG Chat Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # LLM 配置 (OpenAI 兼容模式)
    LLM_API_KEY: Optional[str] = None
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.5-flash"
    
    # Embedding 配置
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    EMBEDDING_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIM: int = 1024
    
    # 向量数据库配置（使用绝对路径）
    CHROMA_PERSIST_DIR: str = os.path.join(BASE_DIR, "storage/chroma")
    
    # 文件存储（使用绝对路径）
    STORAGE_DIR: str = os.path.join(BASE_DIR, "storage/files")
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".doc", ".txt", ".md"}
    
    # 分块配置
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 100
    
    # 检索配置
    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 10
    
    # 安全配置
    SECRET_KEY: str = "change-this-to-a-random-secret-key-in-production"
    
    class Config:
        # 使用绝对路径读取 .env 文件
        env_file = os.path.join(BACKEND_DIR, ".env")
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()


settings = get_settings()