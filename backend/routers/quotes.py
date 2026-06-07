"""Quote-request lead-gen endpoints (public POST + admin inbox CRUD)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from deps import db, require_admin
from models import QuoteCreate, QuoteUpdate

router = APIRouter(tags=["quotes"])


@router.post("/quotes")
async def create_quote(req: QuoteCreate, request: Request):
    """Public — no auth. Anyone viewing a public render can request a quote."""
    quote_id = str(uuid.uuid4())
    viz_ctx = None
    stone_ctx = None
    if req.visualization_id:
        v = await db.visualizations.find_one(
            {"id": req.visualization_id},
            {"_id": 0, "result_image": 0, "kitchen_image": 0},
        )
        if v:
            viz_ctx = {
                "id": v["id"],
                "stone_id": v.get("stone_id"),
                "stone_name": v.get("stone_name"),
            }
            if not req.stone_id:
                req.stone_id = v.get("stone_id")
    if req.stone_id:
        s = await db.house_stones.find_one({"id": req.stone_id}, {"_id": 0})
        if s:
            stone_ctx = {"id": s["id"], "name": s["name"], "type": s["type"]}

    doc = {
        "id": quote_id,
        "name": req.name.strip()[:80],
        "email": req.email.lower().strip(),
        "phone": (req.phone or "").strip()[:40],
        "notes": (req.notes or "").strip()[:2000],
        "visualization_id": req.visualization_id,
        "stone_id": req.stone_id,
        "visualization": viz_ctx,
        "stone": stone_ctx,
        "status": "new",
        "ip": request.client.host if request.client else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.quotes.insert_one(doc)
    return {"id": quote_id, "status": "received"}


@router.get("/admin/quotes")
async def admin_list_quotes(status: Optional[str] = None, _admin=Depends(require_admin)):
    q = {}
    if status:
        q["status"] = status
    cursor = db.quotes.find(q, {"_id": 0}).sort("created_at", -1).limit(200)
    items = await cursor.to_list(200)
    counts_cursor = db.quotes.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])
    counts = {c["_id"]: c["count"] async for c in counts_cursor}
    return {"items": items, "counts": counts}


@router.patch("/admin/quotes/{quote_id}")
async def admin_update_quote(quote_id: str, body: QuoteUpdate, _admin=Depends(require_admin)):
    updates = {}
    if body.status is not None:
        if body.status not in {"new", "contacted", "closed"}:
            raise HTTPException(status_code=400, detail="Invalid status")
        updates["status"] = body.status
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.quotes.find_one_and_update(
        {"id": quote_id}, {"$set": updates}, return_document=True, projection={"_id": 0}
    )
    if not res:
        raise HTTPException(status_code=404, detail="Quote not found")
    return res


@router.delete("/admin/quotes/{quote_id}")
async def admin_delete_quote(quote_id: str, _admin=Depends(require_admin)):
    res = await db.quotes.delete_one({"id": quote_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"deleted": True}
