"""Visualize + visualization gallery + public render permalink + image serving."""
from __future__ import annotations

import base64
import logging
import os
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Depends, Response

from deps import db, get_current_user
from models import VisualizationUpdate, VisualizeReq
from storage import get_object, make_path, put_object
from routers.stones import fetch_stone_payload

logger = logging.getLogger("rated-worktops.visualize")
router = APIRouter(tags=["visualize"])


# ---- Helpers ----
def _strip_data_url(s: str) -> str:
    if not s:
        return s
    if s.startswith("data:"):
        comma = s.find(",")
        if comma >= 0:
            return s[comma + 1:]
    return s


async def _fetch_image_as_b64(url: str) -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url)
        r.raise_for_status()
        return base64.b64encode(r.content).decode("utf-8")


async def _call_gemini_visualize(kitchen_b64: str, stone_b64: str, prompt_text: str) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    chat = LlmChat(
        api_key=os.environ["EMERGENT_LLM_KEY"],
        session_id=f"viz-{uuid.uuid4().hex[:8]}",
        system_message="You are an interior visualization assistant. Apply stone textures to kitchen surfaces realistically.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(
        text=prompt_text,
        file_contents=[ImageContent(kitchen_b64), ImageContent(stone_b64)],
    )
    text, images = await chat.send_message_multimodal_response(msg)
    if not images:
        raise HTTPException(
            status_code=502,
            detail=f"Image generation returned no image. Response: {text[:200] if text else 'empty'}",
        )
    return images[0]["data"]


# ---- Visualize ----
@router.post("/visualize")
async def visualize(req: VisualizeReq, current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["id"]})
    if not user or user.get("credits", 0) < 1:
        raise HTTPException(status_code=402, detail="No credits left. Please buy more credits to continue.")

    stone = await fetch_stone_payload(req.stone_id, current["id"])
    if not stone:
        raise HTTPException(status_code=404, detail="Stone not found")

    kitchen_b64 = _strip_data_url(req.kitchen_image_base64)

    if stone.get("is_custom") and stone.get("image_base64"):
        stone_b64 = _strip_data_url(stone["image_base64"])
    else:
        try:
            stone_b64 = await _fetch_image_as_b64(stone["image_url"])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to load stone reference: {e}")

    extra = (req.instructions or "").strip()
    mode_hint = f" User refinement: {extra}." if req.mode == "hybrid" and extra else ""
    prompt = (
        f"The first image is a customer's real kitchen photograph. The second image is the reference stone material "
        f"'{stone['name']}' ({stone['type']}, {stone['finish']} finish). "
        "Realistically replace the kitchen WORKTOP/COUNTERTOP surfaces and the SPLASHBACK / backsplash wall area "
        "with this exact stone material. Match the original lighting, perspective, reflections and shadows of the kitchen. "
        "Preserve everything else (cabinets, appliances, floor, walls outside the splashback) exactly as in the original. "
        "Keep edges clean and geometry accurate. Output a single photorealistic image of the updated kitchen."
        + mode_hint
    )

    try:
        result_b64 = await _call_gemini_visualize(kitchen_b64, stone_b64, prompt)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Visualize failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)[:200]}")

    res = await db.users.find_one_and_update(
        {"id": current["id"], "credits": {"$gte": 1}},
        {"$inc": {"credits": -1}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=402, detail="No credits left.")

    viz_id = str(uuid.uuid4())
    kitchen_path = None
    result_path = None
    kitchen_image_field = None
    result_image_field = None

    try:
        kitchen_bytes = base64.b64decode(kitchen_b64)
        result_bytes = base64.b64decode(result_b64)
        kitchen_path = await put_object(make_path(viz_id, "kitchen", "jpg"), kitchen_bytes, "image/jpeg")
        result_path = await put_object(make_path(viz_id, "result", "png"), result_bytes, "image/png")
        kitchen_image_field = f"/api/public/renders/{viz_id}/image/kitchen"
        result_image_field = f"/api/public/renders/{viz_id}/image/result"
    except Exception as storage_err:
        logger.warning(f"Storage upload failed, falling back to inline base64: {storage_err}")
        result_image_field = f"data:image/png;base64,{result_b64}"
        kitchen_image_field = (
            req.kitchen_image_base64
            if req.kitchen_image_base64.startswith("data:")
            else f"data:image/jpeg;base64,{kitchen_b64}"
        )

    viz_doc = {
        "id": viz_id,
        "user_id": current["id"],
        "kitchen_image": kitchen_image_field,
        "result_image": result_image_field,
        "kitchen_path": kitchen_path,
        "result_path": result_path,
        "stone_id": stone["id"],
        "stone_name": stone["name"],
        "stone_image": stone["image_url"],
        "mode": req.mode,
        "instructions": extra,
        "published": True,  # default: appears in per-stone showroom
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.visualizations.insert_one(viz_doc)
    viz_doc.pop("_id", None)
    return {"visualization": viz_doc, "credits_remaining": res["credits"]}


# ---- Gallery ----
@router.get("/visualizations")
async def list_visualizations(current=Depends(get_current_user)):
    cursor = (
        db.visualizations.find({"user_id": current["id"]}, {"_id": 0})
        .sort("created_at", -1)
        .limit(60)
    )
    items = await cursor.to_list(60)
    return {"items": items}


@router.patch("/visualizations/{viz_id}")
async def update_visualization(viz_id: str, body: VisualizationUpdate, current=Depends(get_current_user)):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.visualizations.find_one_and_update(
        {"id": viz_id, "user_id": current["id"]},
        {"$set": updates},
        return_document=True,
        projection={"_id": 0},
    )
    if not res:
        raise HTTPException(status_code=404, detail="Visualization not found")
    return res


@router.delete("/visualizations/{viz_id}")
async def delete_visualization(viz_id: str, current=Depends(get_current_user)):
    res = await db.visualizations.delete_one({"id": viz_id, "user_id": current["id"]})
    return {"deleted": res.deleted_count}


# ---- Public render ----
@router.get("/public/renders/{viz_id}")
async def public_render(viz_id: str):
    viz = await db.visualizations.find_one({"id": viz_id}, {"_id": 0})
    if not viz:
        raise HTTPException(status_code=404, detail="Render not found")
    return {
        "id": viz["id"],
        "stone_id": viz.get("stone_id"),
        "stone_name": viz.get("stone_name"),
        "stone_image": viz.get("stone_image"),
        "kitchen_image": viz.get("kitchen_image"),
        "result_image": viz.get("result_image"),
        "mode": viz.get("mode"),
        "created_at": viz.get("created_at"),
    }


@router.get("/public/renders/{viz_id}/image/{kind}")
async def public_render_image(viz_id: str, kind: str):
    if kind not in {"kitchen", "result"}:
        raise HTTPException(status_code=400, detail="Invalid kind")
    viz = await db.visualizations.find_one({"id": viz_id}, {"_id": 0})
    if not viz:
        raise HTTPException(status_code=404, detail="Render not found")
    storage_path = viz.get(f"{kind}_path")
    if not storage_path:
        # Legacy: inline data: URL stored in `{kind}_image`
        data_url = viz.get(f"{kind}_image", "")
        if data_url.startswith("data:"):
            try:
                header, b64 = data_url.split(",", 1)
                ctype = header.split(";")[0][5:] or "image/png"
                return Response(content=base64.b64decode(b64), media_type=ctype)
            except Exception:
                raise HTTPException(status_code=500, detail="Corrupt legacy image")
        raise HTTPException(status_code=404, detail="Image unavailable")
    try:
        content, ctype = await get_object(storage_path)
    except Exception as e:
        logger.exception("Storage fetch failed")
        raise HTTPException(status_code=502, detail=f"Storage error: {str(e)[:120]}")
    return Response(
        content=content,
        media_type=ctype or ("image/png" if kind == "result" else "image/jpeg"),
        headers={"Cache-Control": "public, max-age=86400"},
    )
