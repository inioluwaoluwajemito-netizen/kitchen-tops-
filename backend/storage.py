"""Emergent Object Storage client for Rated Worktops.

We use storage to hold generated kitchen + result images so MongoDB
documents stay small. The DB stores only the storage path; images are
served back through our own backend (/api/public/renders/{id}/image/{kind}).
"""
from __future__ import annotations

import logging
import os
import asyncio
from typing import Optional

import httpx

logger = logging.getLogger("rated-worktops.storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "rated-worktops"

_storage_key: Optional[str] = None
_lock = asyncio.Lock()


async def init_storage(force: bool = False) -> str:
    """Initialize once at startup; reused for the life of the process."""
    global _storage_key
    async with _lock:
        if _storage_key and not force:
            return _storage_key
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            raise RuntimeError("EMERGENT_LLM_KEY missing — cannot init storage")
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{STORAGE_URL}/init", json={"emergent_key": emergent_key})
            r.raise_for_status()
            _storage_key = r.json()["storage_key"]
        logger.info("Object storage initialized")
        return _storage_key


async def put_object(path: str, data: bytes, content_type: str = "image/png") -> str:
    """Upload bytes; returns the canonical storage path."""
    key = await init_storage()
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            content=data,
        )
        # Retry once on 403 (key expired)
        if r.status_code == 403:
            await init_storage(force=True)
            key = _storage_key
            r = await c.put(
                f"{STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key, "Content-Type": content_type},
                content=data,
            )
        r.raise_for_status()
    return r.json()["path"]


async def get_object(path: str) -> tuple[bytes, str]:
    """Download bytes; returns (content, content_type)."""
    key = await init_storage()
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key})
        if r.status_code == 403:
            await init_storage(force=True)
            key = _storage_key
            r = await c.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key})
        r.raise_for_status()
    return r.content, r.headers.get("Content-Type", "application/octet-stream")


def make_path(viz_id: str, kind: str, ext: str = "png") -> str:
    """kind: 'kitchen' or 'result'."""
    return f"{APP_NAME}/renders/{viz_id}/{kind}.{ext}"
