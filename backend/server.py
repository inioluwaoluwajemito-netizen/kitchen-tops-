"""Rated Worktops — FastAPI entry point."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

from deps import db, close_mongo, hash_password, verify_password
from stones_data import STONES
from storage import init_storage
from routers import auth, credits, quotes, stones, visualize

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("rated-worktops")

app = FastAPI(title="Rated Worktops API")
api = APIRouter(prefix="/api")
api.include_router(auth.router)
api.include_router(stones.router)
api.include_router(visualize.router)
api.include_router(quotes.router)
api.include_router(credits.router)


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

# Serve the built frontend app when available (mount /static only, handle SPA routing via catch-all)
frontend_build = ROOT_DIR.parent / "frontend" / "build"
if frontend_build.exists():
    app.mount("/static", StaticFiles(directory=frontend_build / "static"), name="static")


# Serve index.html for all non-API routes (SPA client-side routing)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for client-side routes; let /api routes 404 naturally."""
    if full_path.startswith("api/"):
        # Let API 404s be handled naturally by FastAPI
        from starlette.exceptions import HTTPException
        raise HTTPException(status_code=404, detail="Not Found")
    
    if frontend_build.exists():
        index_path = frontend_build / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    from starlette.exceptions import HTTPException
    raise HTTPException(status_code=404, detail="Not Found")


# ---- Seeders ----
async def _seed_admin():
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
    elif not verify_password(admin_password, existing.get("password_hash", "")):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}},
        )


async def _seed_house_stones():
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


@app.on_event("startup")
async def on_startup():
    # Indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.visualizations.create_index("user_id")
    await db.visualizations.create_index("stone_id")
    await db.custom_stones.create_index("user_id")
    await db.house_stones.create_index("id", unique=True)
    await db.house_stones.create_index("sort_order")
    await db.quotes.create_index("created_at")
    await db.quotes.create_index("status")

    await _seed_admin()
    await _seed_house_stones()

    try:
        await init_storage()
    except Exception as e:
        logger.error(f"Storage init failed: {e}. New renders will fall back to base64-in-Mongo.")


@app.on_event("shutdown")
async def on_shutdown():
    close_mongo()
