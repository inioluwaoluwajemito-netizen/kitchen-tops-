"""Authentication endpoints: email/password + Emergent Google OAuth."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Depends

from deps import (
    db,
    FREE_CREDITS,
    create_access_token,
    get_current_user,
    hash_password,
    user_to_public,
    verify_password,
)
from models import GoogleAuthReq, LoginReq, RegisterReq

logger = logging.getLogger("rated-worktops.auth")
router = APIRouter(tags=["auth"])

EMERGENT_OAUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


@router.post("/auth/register")
async def register(req: RegisterReq):
    email = req.email.lower().strip()
    if await db.users.find_one({"email": email}):
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


@router.post("/auth/login")
async def login(req: LoginReq):
    email = req.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email)
    return {"user": user_to_public(user), "access_token": token}


@router.get("/auth/me")
async def me(current=Depends(get_current_user)):
    return user_to_public(current)


@router.post("/auth/logout")
async def logout(current=Depends(get_current_user)):
    return {"ok": True}


@router.post("/auth/google")
async def google_auth(req: GoogleAuthReq):
    """Exchange an Emergent OAuth session_id for our JWT bearer token."""
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
            "password_hash": "",
            "role": "user",
            "credits": FREE_CREDITS,
            "picture": picture,
            "auth_provider": "google",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(user)
    else:
        if picture and not user.get("picture"):
            await db.users.update_one({"id": user["id"]}, {"$set": {"picture": picture}})

    token = create_access_token(user["id"], email)
    return {"user": user_to_public(user), "access_token": token}
