"""Stones: catalog (house + custom) + admin CRUD + public per-stone showroom."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends

from deps import db, get_current_user, require_admin
from models import CustomStoneCreate, HouseStoneCreate, HouseStoneUpdate

logger = logging.getLogger("rated-worktops.stones")
router = APIRouter(tags=["stones"])


def _house_stone_public(s: dict) -> dict:
    return {
        "id": s["id"],
        "name": s["name"],
        "type": s["type"],
        "finish": s["finish"],
        "origin": s.get("origin", ""),
        "description": s.get("description", ""),
        "image_url": s["image_url"],
        "swatch_color": s.get("swatch_color", "#A1A1A1"),
        "featured": bool(s.get("featured", False)),
    }


# ---- Public ----
@router.get("/public/stones")
async def public_stones(featured_only: bool = False):
    q = {"active": {"$ne": False}}
    if featured_only:
        q["featured"] = True
    cursor = db.house_stones.find(q, {"_id": 0}).sort([("featured", -1), ("sort_order", 1)]).limit(50)
    items = [_house_stone_public(s) for s in await cursor.to_list(50)]
    return {"items": items}


@router.get("/public/stones/{stone_id}")
async def public_stone_detail(stone_id: str):
    s = await db.house_stones.find_one({"id": stone_id, "active": {"$ne": False}}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="Stone not found")
    # Recent published renders that used this stone (latest 8). Payload is URL-only.
    renders_cursor = db.visualizations.find(
        {"stone_id": stone_id, "published": {"$ne": False}},
        {"_id": 0, "id": 1, "created_at": 1, "mode": 1},
    ).sort("created_at", -1).limit(8)
    renders_raw = await renders_cursor.to_list(8)
    renders = [
        {
            "id": r["id"],
            "created_at": r.get("created_at"),
            "mode": r.get("mode"),
            "result_image": f"/api/public/renders/{r['id']}/image/result",
        }
        for r in renders_raw
    ]
    return {"stone": _house_stone_public(s), "renders": renders}


# ---- Authenticated user ----
@router.get("/stones")
async def list_stones(current=Depends(get_current_user)):
    house_cursor = db.house_stones.find({"active": {"$ne": False}}, {"_id": 0}).sort(
        [("featured", -1), ("sort_order", 1)]
    )
    house = [_house_stone_public(s) for s in await house_cursor.to_list(500)]
    custom_cursor = db.custom_stones.find(
        {"user_id": current["id"]}, {"_id": 0, "image_base64": 0}
    )
    custom = await custom_cursor.to_list(200)
    return {"catalog": house, "custom": custom}


@router.post("/stones/custom")
async def add_custom_stone(body: CustomStoneCreate, current=Depends(get_current_user)):
    stone_id = f"custom-{uuid.uuid4().hex[:10]}"
    doc = {
        "id": stone_id,
        "user_id": current["id"],
        "name": body.name.strip()[:60],
        "type": body.type[:30],
        "finish": body.finish[:30],
        "image_base64": body.image_base64,
        "image_url": body.image_base64,
        "is_custom": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.custom_stones.insert_one(doc)
    return {
        "id": stone_id,
        "name": doc["name"],
        "type": doc["type"],
        "finish": doc["finish"],
        "image_url": doc["image_url"],
        "is_custom": True,
    }


async def fetch_stone_payload(stone_id: str, user_id: str):
    """Used by /api/visualize to resolve a stone reference. House or custom."""
    s = await db.house_stones.find_one({"id": stone_id}, {"_id": 0})
    if s:
        return {
            "id": s["id"],
            "name": s["name"],
            "type": s["type"],
            "finish": s["finish"],
            "image_url": s["image_url"],
            "is_custom": False,
        }
    cs = await db.custom_stones.find_one({"id": stone_id, "user_id": user_id})
    if cs:
        return {
            "id": cs["id"],
            "name": cs["name"],
            "type": cs["type"],
            "finish": cs["finish"],
            "image_url": cs.get("image_url") or cs.get("image_base64"),
            "image_base64": cs.get("image_base64"),
            "is_custom": True,
        }
    return None


# ---- Admin ----
@router.get("/admin/stones")
async def admin_list_stones(_admin=Depends(require_admin)):
    cursor = db.house_stones.find({}, {"_id": 0}).sort("sort_order", 1)
    return {"items": await cursor.to_list(500)}


@router.post("/admin/stones")
async def admin_create_stone(body: HouseStoneCreate, _admin=Depends(require_admin)):
    stone_id = body.name.lower().strip().replace(" ", "-")[:40] + "-" + uuid.uuid4().hex[:4]
    last = await db.house_stones.find_one({}, sort=[("sort_order", -1)])
    next_order = (last.get("sort_order", 0) + 1) if last else 1
    doc = {
        "id": stone_id,
        "name": body.name.strip(),
        "type": body.type.strip(),
        "finish": body.finish.strip(),
        "origin": body.origin.strip(),
        "description": body.description.strip(),
        "image_url": body.image_url.strip(),
        "swatch_color": body.swatch_color.strip(),
        "featured": bool(body.featured),
        "active": True,
        "sort_order": next_order,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.house_stones.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/admin/stones/{stone_id}")
async def admin_update_stone(stone_id: str, body: HouseStoneUpdate, _admin=Depends(require_admin)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.house_stones.find_one_and_update(
        {"id": stone_id}, {"$set": updates}, return_document=True, projection={"_id": 0}
    )
    if not res:
        raise HTTPException(status_code=404, detail="Stone not found")
    return res


@router.delete("/admin/stones/{stone_id}")
async def admin_delete_stone(stone_id: str, _admin=Depends(require_admin)):
    res = await db.house_stones.delete_one({"id": stone_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Stone not found")
    return {"deleted": True}
