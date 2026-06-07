"""Credit balance + (mocked) purchase endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from deps import db, get_current_user
from models import PurchaseReq

router = APIRouter(tags=["credits"])

CREDIT_PACKS = {
    "starter": {"id": "starter", "name": "Starter", "credits": 10, "price_gbp": 5, "popular": False},
    "pro": {"id": "pro", "name": "Pro", "credits": 30, "price_gbp": 12, "popular": True},
    "studio": {"id": "studio", "name": "Studio", "credits": 100, "price_gbp": 35, "popular": False},
}

VALID_METHODS = {"paypal", "apple_pay", "google_pay"}


@router.get("/credits")
async def get_credits(current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["id"]}, {"_id": 0, "password_hash": 0})
    txns_cursor = (
        db.credit_transactions.find({"user_id": current["id"]}, {"_id": 0})
        .sort("created_at", -1)
        .limit(20)
    )
    txns = await txns_cursor.to_list(20)
    return {
        "balance": user.get("credits", 0) if user else 0,
        "packs": list(CREDIT_PACKS.values()),
        "transactions": txns,
    }


@router.post("/credits/purchase")
async def purchase_credits(req: PurchaseReq, current=Depends(get_current_user)):
    pack = CREDIT_PACKS.get(req.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail="Invalid pack")
    if req.method not in VALID_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # MOCKED PAYMENT — real PayPal sandbox can be wired here once credentials are provided
    updated = await db.users.find_one_and_update(
        {"id": current["id"]},
        {"$inc": {"credits": pack["credits"]}},
        return_document=True,
    )
    txn = {
        "id": str(uuid.uuid4()),
        "user_id": current["id"],
        "pack_id": pack["id"],
        "pack_name": pack["name"],
        "credits": pack["credits"],
        "price_gbp": pack["price_gbp"],
        "method": req.method,
        "status": "mocked_success",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.credit_transactions.insert_one(txn)
    txn.pop("_id", None)
    return {"balance": updated["credits"], "transaction": txn, "mocked": True}
