"""知识库元数据存储服务"""
import asyncio
import inspect
import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, TypeVar

import aiofiles

from app.core.config import settings


T = TypeVar("T")


class MetadataStoreError(RuntimeError):
    """元数据文件读取或写入失败"""


class MetadataStore:
    """串行、原子地读写 kb_metadata.json。"""

    def __init__(self):
        self._lock = asyncio.Lock()

    @property
    def metadata_file(self) -> str:
        return os.path.join(settings.STORAGE_DIR, "kb_metadata.json")

    async def load(self) -> Dict[str, Any]:
        """加载元数据快照。"""
        async with self._lock:
            return await self._read_unlocked()

    async def update(self, mutator: Callable[[Dict[str, Any]], T]) -> T:
        """在锁内执行读改写，避免并发覆盖。"""
        async with self._lock:
            data = await self._read_unlocked()
            result = mutator(data)
            if inspect.isawaitable(result):
                result = await result
            await self._write_unlocked(data)
            return result

    async def _read_unlocked(self) -> Dict[str, Any]:
        path = self.metadata_file
        if not os.path.exists(path):
            return {}

        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                content = await f.read()
        except OSError as e:
            raise MetadataStoreError(f"读取元数据文件失败: {e}") from e

        if not content.strip():
            return {}

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            backup_path = self._backup_corrupt_file(path)
            raise MetadataStoreError(
                f"元数据文件损坏，已保留备份: {backup_path}"
            ) from e

    async def _write_unlocked(self, data: Dict[str, Any]) -> None:
        path = self.metadata_file
        os.makedirs(os.path.dirname(path), exist_ok=True)

        tmp_path = f"{path}.{uuid.uuid4().hex}.tmp"
        try:
            async with aiofiles.open(tmp_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                await f.flush()
            os.replace(tmp_path, path)
        except OSError as e:
            raise MetadataStoreError(f"保存元数据文件失败: {e}") from e
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _backup_corrupt_file(self, path: str) -> str:
        backup_path = f"{path}.corrupt.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            shutil.copy2(path, backup_path)
        except OSError as e:
            raise MetadataStoreError(f"备份损坏元数据文件失败: {e}") from e
        return backup_path


metadata_store = MetadataStore()
