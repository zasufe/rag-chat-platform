import asyncio
import os
import shutil
import tempfile
import unittest
from datetime import datetime

from app.core.config import settings
from app.services.metadata_store import MetadataStore, MetadataStoreError


class MetadataStoreTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_storage_dir = settings.STORAGE_DIR
        self.storage_dir = tempfile.mkdtemp()
        settings.STORAGE_DIR = self.storage_dir
        self.store = MetadataStore()

    def tearDown(self):
        settings.STORAGE_DIR = self.original_storage_dir
        shutil.rmtree(self.storage_dir, ignore_errors=True)

    async def test_concurrent_document_adds_keep_all_records(self):
        kb_id = "kb-test"

        def create_kb(metadata: dict):
            now = datetime.now().isoformat()
            metadata[kb_id] = {
                "id": kb_id,
                "name": "测试知识库",
                "document_count": 0,
                "total_chunks": 0,
                "created_at": now,
                "updated_at": now,
                "documents": {}
            }

        await self.store.update(create_kb)

        async def add_doc(index: int):
            def mutate(metadata: dict):
                doc_id = f"doc-{index}"
                metadata[kb_id]["documents"][doc_id] = {
                    "doc_id": doc_id,
                    "filename": f"{index}.txt",
                    "file_size": index,
                    "chunks_count": 0,
                    "mime_type": "text/plain",
                    "uploaded_at": datetime.now().isoformat(),
                    "status": "processing",
                    "description": None
                }

            await self.store.update(mutate)

        await asyncio.gather(*(add_doc(i) for i in range(10)))

        metadata = await self.store.load()
        self.assertEqual(len(metadata[kb_id]["documents"]), 10)

    async def test_concurrent_status_updates_do_not_drop_documents(self):
        kb_id = "kb-test"

        def seed(metadata: dict):
            now = datetime.now().isoformat()
            metadata[kb_id] = {
                "id": kb_id,
                "name": "测试知识库",
                "document_count": 0,
                "total_chunks": 0,
                "created_at": now,
                "updated_at": now,
                "documents": {
                    f"doc-{i}": {
                        "doc_id": f"doc-{i}",
                        "filename": f"{i}.txt",
                        "file_size": i,
                        "chunks_count": 0,
                        "mime_type": "text/plain",
                        "uploaded_at": now,
                        "status": "processing",
                        "description": None
                    }
                    for i in range(8)
                }
            }

        await self.store.update(seed)

        async def complete_doc(index: int):
            def mutate(metadata: dict):
                doc = metadata[kb_id]["documents"][f"doc-{index}"]
                doc["status"] = "completed" if index % 2 == 0 else "failed"
                doc["chunks_count"] = index

            await self.store.update(mutate)

        await asyncio.gather(*(complete_doc(i) for i in range(8)))

        metadata = await self.store.load()
        documents = metadata[kb_id]["documents"]
        self.assertEqual(len(documents), 8)
        self.assertEqual(documents["doc-6"]["chunks_count"], 6)
        self.assertEqual(documents["doc-7"]["status"], "failed")

    async def test_corrupt_json_is_not_treated_as_empty_metadata(self):
        os.makedirs(settings.STORAGE_DIR, exist_ok=True)
        metadata_path = os.path.join(settings.STORAGE_DIR, "kb_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        with self.assertRaises(MetadataStoreError):
            await self.store.load()

        backups = [
            name for name in os.listdir(settings.STORAGE_DIR)
            if name.startswith("kb_metadata.json.corrupt.")
        ]
        self.assertTrue(backups)
        self.assertTrue(os.path.exists(metadata_path))


if __name__ == "__main__":
    unittest.main()
