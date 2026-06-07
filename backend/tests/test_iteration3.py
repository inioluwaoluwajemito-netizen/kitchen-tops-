"""Iteration 3 tests: Object storage migration + per-stone showroom page.

Covers:
- POST /api/visualize uploads to storage, returns backend URLs (not data URLs)
- GET /api/public/renders/{id}/image/{kind} serves actual bytes (200, image/*)
- Invalid kind -> 400, bogus id -> 404
- Legacy backward-compat: docs with data: URL inline still serve via /image/{kind}
- GET /api/public/stones/{id}: active stone returns stone+renders; inactive/bogus -> 404
- Mongo doc size: new visualization docs are tiny (<5 KB)
- Regression smoke: /api/stones, /api/auth/login, /api/admin/stones, /api/admin/quotes,
  /api/credits/purchase (paypal/apple_pay/google_pay) still work.
"""
import base64
import os
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    fe = Path("/app/frontend/.env").read_text()
    for line in fe.splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@ratedworktops.com"
ADMIN_PASS = "Admin@RW2026"

# 1x1 px white JPEG (tiny but valid)
TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA//"
    "2Q=="
)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def session():
    return requests.Session()


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def user_token(session):
    email = f"it3_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": "Test@1234", "name": "It3 User"},
    )
    assert r.status_code == 200
    return r.json()["access_token"]


# =========== Storage-backed visualize (one real Gemini call) ===========
@pytest.fixture(scope="module")
def fresh_viz(session, user_token):
    """One real Gemini visualize → returns the new viz response."""
    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": "carrara-white",
        "mode": "auto",
        "instructions": "",
    }
    r = session.post(f"{API}/visualize", json=payload, headers=auth(user_token), timeout=180)
    assert r.status_code == 200, f"visualize failed: {r.status_code} {r.text[:400]}"
    return r.json()["visualization"]


def test_visualize_response_uses_storage_urls(fresh_viz):
    viz = fresh_viz
    # Backend URLs (not data: URLs)
    assert viz["kitchen_image"] == f"/api/public/renders/{viz['id']}/image/kitchen"
    assert viz["result_image"] == f"/api/public/renders/{viz['id']}/image/result"
    assert not viz["kitchen_image"].startswith("data:")
    assert not viz["result_image"].startswith("data:")


def test_visualize_response_has_storage_paths(fresh_viz):
    viz = fresh_viz
    assert viz.get("kitchen_path"), "kitchen_path missing"
    assert viz.get("result_path"), "result_path missing"
    # Expected canonical path shape
    assert viz["kitchen_path"].startswith(f"rated-worktops/renders/{viz['id']}/")
    assert viz["result_path"].startswith(f"rated-worktops/renders/{viz['id']}/")
    assert viz["kitchen_path"].endswith("/kitchen.jpg")
    assert viz["result_path"].endswith("/result.png")


def test_public_image_result_returns_bytes(session, fresh_viz):
    viz_id = fresh_viz["id"]
    r = session.get(f"{API}/public/renders/{viz_id}/image/result", timeout=60)
    assert r.status_code == 200
    ctype = r.headers.get("Content-Type", "")
    assert ctype.startswith("image/"), f"expected image/* got {ctype}"
    assert len(r.content) > 1000, f"expected non-empty bytes, got {len(r.content)}"
    # Backend sets Cache-Control: public, max-age=86400; note: ingress may rewrite.
    # We don't assert on it because Cloudflare/ingress override is out of our control.


def test_public_image_kitchen_returns_bytes(session, fresh_viz):
    viz_id = fresh_viz["id"]
    r = session.get(f"{API}/public/renders/{viz_id}/image/kitchen", timeout=60)
    assert r.status_code == 200
    assert r.headers.get("Content-Type", "").startswith("image/")
    assert len(r.content) > 100


def test_public_image_invalid_kind_returns_400(session, fresh_viz):
    r = session.get(f"{API}/public/renders/{fresh_viz['id']}/image/INVALID")
    assert r.status_code == 400


def test_public_image_bogus_id_returns_404(session):
    r = session.get(f"{API}/public/renders/bogus-id-{uuid.uuid4().hex}/image/result")
    assert r.status_code == 404


# =========== Mongo doc size check ===========
@pytest.mark.asyncio
async def test_visualization_doc_is_small(fresh_viz):
    """Ensure new docs do not embed base64 blobs (was ~700KB; should be <5KB)."""
    import bson
    mongo_url = os.environ["MONGO_URL"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ["DB_NAME"]]
    doc = await db.visualizations.find_one({"id": fresh_viz["id"]})
    client.close()
    assert doc is not None
    size = len(bson.BSON.encode(doc))
    assert size < 5_000, f"visualization doc too large: {size} bytes (expected <5KB; base64 blobs?)"


# =========== Legacy backward-compat: data: URL inline ===========
@pytest.mark.asyncio
async def test_legacy_inline_image_served(session, user_token):
    """Insert a synthetic legacy doc (no *_path, only data: URLs) and verify /image/{kind}
    decodes and serves it.
    """
    mongo_url = os.environ["MONGO_URL"]
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ["DB_NAME"]]
    # 1x1 PNG (red pixel) — tiny but valid
    png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
        "IQAAAABJRU5ErkJggg=="
    )
    legacy_id = f"legacy-{uuid.uuid4().hex[:10]}"
    await db.visualizations.insert_one({
        "id": legacy_id,
        "user_id": "legacy",
        "kitchen_image": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "result_image": f"data:image/png;base64,{png_b64}",
        # NB: no kitchen_path / result_path on purpose
        "stone_id": "carrara-white",
        "stone_name": "Legacy",
        "mode": "auto",
        "created_at": "2025-01-01T00:00:00+00:00",
    })
    try:
        r1 = session.get(f"{API}/public/renders/{legacy_id}/image/result")
        assert r1.status_code == 200, f"result: {r1.status_code} {r1.text[:200]}"
        assert r1.headers.get("Content-Type", "").startswith("image/")
        assert r1.content == base64.b64decode(png_b64)

        r2 = session.get(f"{API}/public/renders/{legacy_id}/image/kitchen")
        assert r2.status_code == 200, f"kitchen: {r2.status_code}"
        assert r2.headers.get("Content-Type", "").startswith("image/")
        assert r2.content == base64.b64decode(TINY_JPEG_B64)
    finally:
        await db.visualizations.delete_one({"id": legacy_id})
        client.close()


# =========== Per-stone showroom page ===========
def test_public_stone_detail_active(session):
    r = session.get(f"{API}/public/stones/carrara-white")
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    data = r.json()
    assert "stone" in data and "renders" in data
    stone = data["stone"]
    for k in ["id", "name", "type", "finish", "image_url", "featured", "description", "origin"]:
        assert k in stone, f"missing field {k}"
    assert stone["id"] == "carrara-white"
    assert isinstance(stone["featured"], bool)
    assert isinstance(data["renders"], list)


def test_public_stone_detail_bogus_returns_404(session):
    r = session.get(f"{API}/public/stones/bogus-{uuid.uuid4().hex}")
    assert r.status_code == 404


def test_public_stone_detail_inactive_returns_404(session, admin_token):
    # Create an inactive stone, fetch it -> expect 404, then cleanup.
    create = session.post(
        f"{API}/admin/stones",
        json={
            "name": f"TEST_Inactive_{uuid.uuid4().hex[:6]}",
            "type": "Test",
            "finish": "Test",
            "origin": "Lab",
            "description": "Inactive test stone",
            "image_url": "https://example.com/x.jpg",
            "swatch_color": "#000000",
            "featured": False,
        },
        headers=auth(admin_token),
    )
    assert create.status_code == 200, create.text
    sid = create.json()["id"]
    try:
        # Confirm visible while active
        r_active = session.get(f"{API}/public/stones/{sid}")
        assert r_active.status_code == 200
        # Deactivate
        patch = session.patch(
            f"{API}/admin/stones/{sid}",
            json={"active": False},
            headers=auth(admin_token),
        )
        assert patch.status_code == 200
        # Now should 404
        r_inact = session.get(f"{API}/public/stones/{sid}")
        assert r_inact.status_code == 404
    finally:
        session.delete(f"{API}/admin/stones/{sid}", headers=auth(admin_token))


# =========== Regression smoke ===========
def test_regression_list_stones_auth(session, user_token):
    r = session.get(f"{API}/stones", headers=auth(user_token))
    assert r.status_code == 200
    body = r.json()
    assert "catalog" in body and "custom" in body
    assert len(body["catalog"]) >= 1


def test_regression_admin_list_stones(session, admin_token):
    r = session.get(f"{API}/admin/stones", headers=auth(admin_token))
    assert r.status_code == 200
    assert "items" in r.json()


def test_regression_admin_list_quotes(session, admin_token):
    r = session.get(f"{API}/admin/quotes", headers=auth(admin_token))
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "counts" in body


def test_regression_quote_create_no_auth(session):
    r = session.post(
        f"{API}/quotes",
        json={"name": "TEST_It3", "email": "it3@example.com", "stone_id": "carrara-white"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "received"


@pytest.mark.parametrize("method", ["paypal", "apple_pay", "google_pay"])
def test_regression_purchase_methods(session, user_token, method):
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "starter", "method": method},
        headers=auth(user_token),
    )
    assert r.status_code == 200, f"{method}: {r.status_code} {r.text}"
    body = r.json()
    assert body["mocked"] is True
    assert body["balance"] >= 10
