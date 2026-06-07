"""Rated Worktops — FastAPI backend."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import base64
import logging
import uuid
import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, List

import bcrypt
import jwt
from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field

from stones_data import STONES, get_stone_by_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("rated-worktops")

# Mongo
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
FREE_CREDITS = int(os.environ.get("FREE_CREDITS", "3"))

app = FastAPI(title="Rated Worktops API")
api = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)


# ============ Helpers ============
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def user_to_public(u: dict) -> dict:
    return {
        "id": u["id"],
        "email": u["email"],
        "name": u.get("name", ""),
        "role": u.get("role", "user"),
        "credits": u.get("credits", 0),
        "created_at": u.get("created_at"),
    }


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> dict:
    token = None
    if creds and creds.scheme.lower() == "bearer":
        token = creds.credentials
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ============ Models ============
class RegisterReq(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=80)


class LoginReq(BaseModel):
    email: EmailStr
    password: str


class VisualizeReq(BaseModel):
    kitchen_image_base64: str  # data URL or raw base64
    stone_id: str
    mode: str = "auto"  # auto | hybrid
    instructions: Optional[str] = ""


class PurchaseReq(BaseModel):
    pack_id: str  # starter | pro | studio
    method: str  # stripe | paypal | apple_pay | google_pay


class CustomStoneCreate(BaseModel):
    name: str
    type: str = "Custom"
    finish: str = "Custom"
    image_base64: str


class HouseStoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=40)
    finish: str = Field(min_length=1, max_length=40)
    origin: str = ""
    description: str = ""
    image_url: str = Field(min_length=1)
    swatch_color: str = "#A1A1A1"
    featured: bool = False


class HouseStoneUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    finish: Optional[str] = None
    origin: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    swatch_color: Optional[str] = None
    active: Optional[bool] = None
    featured: Optional[bool] = None


class GoogleAuthReq(BaseModel):
    session_id: str


class QuoteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    phone: Optional[str] = ""
    notes: Optional[str] = ""
    visualization_id: Optional[str] = None
    stone_id: Optional[str] = None


class QuoteUpdate(BaseModel):
    status: Optional[str] = None  # new | contacted | closed


async def require_admin(current=Depends(get_current_user)) -> dict:
    if current.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return current


# ============ Auth Endpoints ============
@api.post("/auth/register")
async def register(req: RegisterReq):
    email = req.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = str(uuid.uuid4())
    doc = {
        "id": user_id,
        "email": email,
        "name": req.name.strip(),
        "password_hash": hash_password(req.password),
        "role": "user",
        "credits": FREE_CREDITS,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(doc)
    token = create_access_token(user_id, email)
    doc.pop("password_hash")
    return {"user": user_to_public(doc), "access_token": token}


@api.post("/auth/login")
async def login(req: LoginReq):
    email = req.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    return {"user": user_to_public(user), "access_token": token}


@api.get("/auth/me")
async def me(current=Depends(get_current_user)):
    return user_to_public(current)


@api.post("/auth/logout")
async def logout(current=Depends(get_current_user)):
    return {"ok": True}


# ============ Emergent Google Auth ============
EMERGENT_OAUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


@api.post("/auth/google")
async def google_auth(req: GoogleAuthReq):
    """Exchange Emergent session_id for our own JWT bearer token."""
    if not req.session_id or len(req.session_id) < 8:
        raise HTTPException(status_code=400, detail="Missing session_id")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(EMERGENT_OAUTH_URL, headers={"X-Session-ID": req.session_id})
        if r.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google session")
        profile = r.json()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Google auth exchange failed")
        raise HTTPException(status_code=502, detail=f"Google auth failed: {str(e)[:120]}")

    email = (profile.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google did not return an email")
    name = profile.get("name") or email.split("@")[0]
    picture = profile.get("picture") or ""

    user = await db.users.find_one({"email": email})
    if user is None:
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "password_hash": "",  # OAuth user — no password
            "role": "user",
            "credits": FREE_CREDITS,
            "picture": picture,
            "auth_provider": "google",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user)
    else:
        # Update profile picture if missing
        if picture and not user.get("picture"):
            await db.users.update_one({"id": user["id"]}, {"$set": {"picture": picture}})

    token = create_access_token(user["id"], email)
    return {"user": user_to_public(user), "access_token": token}


# ============ Stones ============
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


@api.get("/public/stones")
async def public_stones(featured_only: bool = False):
    q = {"active": {"$ne": False}}
    if featured_only:
        q["featured"] = True
    cursor = db.house_stones.find(q, {"_id": 0}).sort([("featured", -1), ("sort_order", 1)]).limit(50)
    items = [_house_stone_public(s) for s in await cursor.to_list(50)]
    return {"items": items}


@api.get("/stones")
async def list_stones(current=Depends(get_current_user)):
    house_cursor = db.house_stones.find({"active": {"$ne": False}}, {"_id": 0}).sort([("featured", -1), ("sort_order", 1)])
    house = [_house_stone_public(s) for s in await house_cursor.to_list(500)]
    custom_cursor = db.custom_stones.find({"user_id": current["id"]}, {"_id": 0, "image_base64": 0})
    custom = await custom_cursor.to_list(200)
    return {"catalog": house, "custom": custom}


@api.post("/stones/custom")
async def add_custom_stone(body: CustomStoneCreate, current=Depends(get_current_user)):
    stone_id = f"custom-{uuid.uuid4().hex[:10]}"
    doc = {
        "id": stone_id,
        "user_id": current["id"],
        "name": body.name.strip()[:60],
        "type": body.type[:30],
        "finish": body.finish[:30],
        "image_base64": body.image_base64,
        "image_url": body.image_base64,  # data URL works as preview src
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


# ============ Admin: house catalog management ============
@api.get("/admin/stones")
async def admin_list_stones(_admin=Depends(require_admin)):
    cursor = db.house_stones.find({}, {"_id": 0}).sort("sort_order", 1)
    items = await cursor.to_list(500)
    return {"items": items}


@api.post("/admin/stones")
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


@api.patch("/admin/stones/{stone_id}")
async def admin_update_stone(stone_id: str, body: HouseStoneUpdate, _admin=Depends(require_admin)):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    res = await db.house_stones.find_one_and_update(
        {"id": stone_id}, {"$set": updates}, return_document=True, projection={"_id": 0}
    )
    if not res:
        raise HTTPException(status_code=404, detail="Stone not found")
    return res


@api.delete("/admin/stones/{stone_id}")
async def admin_delete_stone(stone_id: str, _admin=Depends(require_admin)):
    res = await db.house_stones.delete_one({"id": stone_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Stone not found")
    return {"deleted": True}


# ============ Image generation (Gemini Nano Banana) ============
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


async def call_gemini_visualize(kitchen_b64: str, stone_b64: str, prompt_text: str) -> str:
    """Call Gemini Nano Banana via emergentintegrations. Returns base64 PNG."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = os.environ["EMERGENT_LLM_KEY"]
    chat = LlmChat(
        api_key=api_key,
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
        raise HTTPException(status_code=502, detail=f"Image generation returned no image. Response: {text[:200] if text else 'empty'}")
    return images[0]["data"]  # base64 string


@api.post("/visualize")
async def visualize(req: VisualizeReq, current=Depends(get_current_user)):
    # Check credits
    user = await db.users.find_one({"id": current["id"]})
    if not user or user.get("credits", 0) < 1:
        raise HTTPException(status_code=402, detail="No credits left. Please buy more credits to continue.")

    stone = await fetch_stone_payload(req.stone_id, current["id"])
    if not stone:
        raise HTTPException(status_code=404, detail="Stone not found")

    kitchen_b64 = _strip_data_url(req.kitchen_image_base64)

    # Get stone texture as base64
    if stone.get("is_custom") and stone.get("image_base64"):
        stone_b64 = _strip_data_url(stone["image_base64"])
    else:
        try:
            stone_b64 = await _fetch_image_as_b64(stone["image_url"])
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to load stone reference: {e}")

    # Build prompt
    extra = (req.instructions or "").strip()
    mode_hint = ""
    if req.mode == "hybrid" and extra:
        mode_hint = f" User refinement: {extra}."

    prompt = (
        f"The first image is a customer's real kitchen photograph. The second image is the reference stone material '{stone['name']}' ({stone['type']}, {stone['finish']} finish). "
        "Realistically replace the kitchen WORKTOP/COUNTERTOP surfaces and the SPLASHBACK / backsplash wall area with this exact stone material. "
        "Match the original lighting, perspective, reflections and shadows of the kitchen. Preserve everything else (cabinets, appliances, floor, walls outside the splashback) exactly as in the original. "
        "Keep edges clean and geometry accurate. Output a single photorealistic image of the updated kitchen."
        + mode_hint
    )

    try:
        result_b64 = await call_gemini_visualize(kitchen_b64, stone_b64, prompt)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Visualize failed")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)[:200]}")

    # Deduct credit (atomic)
    res = await db.users.find_one_and_update(
        {"id": current["id"], "credits": {"$gte": 1}},
        {"$inc": {"credits": -1}},
        return_document=True,
    )
    if not res:
        raise HTTPException(status_code=402, detail="No credits left.")

    viz_id = str(uuid.uuid4())
    result_data_url = f"data:image/png;base64,{result_b64}"
    kitchen_data_url = req.kitchen_image_base64 if req.kitchen_image_base64.startswith("data:") else f"data:image/jpeg;base64,{kitchen_b64}"

    viz_doc = {
        "id": viz_id,
        "user_id": current["id"],
        "kitchen_image": kitchen_data_url,
        "result_image": result_data_url,
        "stone_id": stone["id"],
        "stone_name": stone["name"],
        "stone_image": stone["image_url"],
        "mode": req.mode,
        "instructions": extra,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.visualizations.insert_one(viz_doc)
    viz_doc.pop("_id", None)
    return {
        "visualization": viz_doc,
        "credits_remaining": res["credits"],
    }


@api.get("/visualizations")
async def list_visualizations(current=Depends(get_current_user)):
    cursor = db.visualizations.find({"user_id": current["id"]}, {"_id": 0}).sort("created_at", -1).limit(60)
    items = await cursor.to_list(60)
    return {"items": items}


@api.delete("/visualizations/{viz_id}")
async def delete_visualization(viz_id: str, current=Depends(get_current_user)):
    res = await db.visualizations.delete_one({"id": viz_id, "user_id": current["id"]})
    return {"deleted": res.deleted_count}


# ============ Public render permalink ============
@api.get("/public/renders/{viz_id}")
async def public_render(viz_id: str):
    viz = await db.visualizations.find_one({"id": viz_id}, {"_id": 0})
    if not viz:
        raise HTTPException(status_code=404, detail="Render not found")
    # Strip internal fields, expose only what a public viewer needs
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


# ============ Quote requests (lead-gen) ============
@api.post("/quotes")
async def create_quote(req: QuoteCreate, request: Request):
    """Public — no auth required. Anyone viewing a render can request a quote."""
    quote_id = str(uuid.uuid4())
    # Capture context if visualization provided
    viz_ctx = None
    stone_ctx = None
    if req.visualization_id:
        v = await db.visualizations.find_one({"id": req.visualization_id}, {"_id": 0, "result_image": 0, "kitchen_image": 0})
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


@api.get("/admin/quotes")
async def admin_list_quotes(status: Optional[str] = None, _admin=Depends(require_admin)):
    q = {}
    if status:
        q["status"] = status
    cursor = db.quotes.find(q, {"_id": 0}).sort("created_at", -1).limit(200)
    items = await cursor.to_list(200)
    counts_cursor = db.quotes.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])
    counts = {c["_id"]: c["count"] async for c in counts_cursor}
    return {"items": items, "counts": counts}


@api.patch("/admin/quotes/{quote_id}")
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


@api.delete("/admin/quotes/{quote_id}")
async def admin_delete_quote(quote_id: str, _admin=Depends(require_admin)):
    res = await db.quotes.delete_one({"id": quote_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Quote not found")
    return {"deleted": True}


# ============ Credits ============
CREDIT_PACKS = {
    "starter": {"id": "starter", "name": "Starter", "credits": 10, "price_gbp": 5, "popular": False},
    "pro": {"id": "pro", "name": "Pro", "credits": 30, "price_gbp": 12, "popular": True},
    "studio": {"id": "studio", "name": "Studio", "credits": 100, "price_gbp": 35, "popular": False},
}


@api.get("/credits")
async def get_credits(current=Depends(get_current_user)):
    user = await db.users.find_one({"id": current["id"]}, {"_id": 0, "password_hash": 0})
    txns_cursor = db.credit_transactions.find({"user_id": current["id"]}, {"_id": 0}).sort("created_at", -1).limit(20)
    txns = await txns_cursor.to_list(20)
    return {
        "balance": user.get("credits", 0) if user else 0,
        "packs": list(CREDIT_PACKS.values()),
        "transactions": txns,
    }


@api.post("/credits/purchase")
async def purchase_credits(req: PurchaseReq, current=Depends(get_current_user)):
    pack = CREDIT_PACKS.get(req.pack_id)
    if not pack:
        raise HTTPException(status_code=400, detail="Invalid pack")
    if req.method not in {"paypal", "apple_pay", "google_pay"}:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # MOCKED PAYMENT - in production, integrate Stripe/PayPal here
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


@api.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.visualizations.create_index("user_id")
    await db.custom_stones.create_index("user_id")
    await db.house_stones.create_index("id", unique=True)
    await db.house_stones.create_index("sort_order")
    await db.quotes.create_index("created_at")
    await db.quotes.create_index("status")

    # Seed house_stones from stones_data.py if collection is empty
    if await db.house_stones.count_documents({}) == 0:
        for i, s in enumerate(STONES):
            await db.house_stones.insert_one({
                "id": s["id"],
                "name": s["name"],
                "type": s["type"],
                "finish": s["finish"],
                "origin": s.get("origin", ""),
                "description": s.get("description", ""),
                "image_url": s["image_url"],
                "swatch_color": s.get("swatch_color", "#A1A1A1"),
                "active": True,
                "sort_order": i + 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        logger.info(f"Seeded {len(STONES)} house stones")

    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@ratedworktops.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@RW2026")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "name": "Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "credits": 9999,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Seeded admin {admin_email}")
    else:
        # Re-sync password if changed in env
        if not verify_password(admin_password, existing.get("password_hash", "")):
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {"password_hash": hash_password(admin_password)}},
            )


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
