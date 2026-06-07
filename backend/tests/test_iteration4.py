"""Iteration 4 tests: refactor sanity + PATCH /api/visualizations/{id} + published filter.

Covers:
- /api/health still 200 (server.py shim still mounts it)
- Real Gemini call ONCE creates viz with published=True (response + Mongo doc)
- PATCH /visualizations/{id} {published: False} as owner -> returns updated doc
- PATCH /visualizations/{id} as different user -> 404
- PATCH /visualizations/bogus-id -> 404
- PATCH with empty body {} -> 400
- After published=False, /api/public/stones/{stone_id} renders array excludes the viz id
- Setting published=True again restores visibility in the showroom (latest 8)
- Per-stone showroom respects the 8-render cap and doesn't crash on empty
- Regression: previous endpoints still wired (cross-referenced by other suites)
"""
import asyncio
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
STONE_ID = "carrara-white"

# 1x1 px white JPEG
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
def owner_token(session):
    email = f"it4owner_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": "Test@1234", "name": "It4 Owner"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def other_token(session):
    email = f"it4other_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(
        f"{API}/auth/register",
        json={"email": email, "password": "Test@1234", "name": "It4 Other"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


# Sanity / health -------------------------------------------------------------
def test_health_still_200(session):
    r = session.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# One real Gemini call --------------------------------------------------------
@pytest.fixture(scope="module")
def fresh_viz(session, owner_token):
    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": STONE_ID,
        "mode": "auto",
        "instructions": "",
    }
    r = session.post(f"{API}/visualize", json=payload, headers=auth(owner_token), timeout=180)
    assert r.status_code == 200, f"visualize failed: {r.status_code} {r.text[:400]}"
    return r.json()["visualization"]


def test_new_viz_published_true_in_response(fresh_viz):
    assert fresh_viz.get("published") is True, fresh_viz


def test_new_viz_published_true_in_mongo(fresh_viz):
    mongo_url = os.environ["MONGO_URL"]
    db_name = os.environ["DB_NAME"]

    async def _check():
        client = AsyncIOMotorClient(mongo_url)
        try:
            doc = await client[db_name].visualizations.find_one({"id": fresh_viz["id"]})
            assert doc is not None
            assert doc.get("published") is True
        finally:
            client.close()

    asyncio.run(_check())


# PATCH endpoint --------------------------------------------------------------
def test_patch_bogus_id_returns_404(session, owner_token):
    r = session.patch(
        f"{API}/visualizations/bogus-id-{uuid.uuid4().hex}",
        json={"published": False},
        headers=auth(owner_token),
    )
    assert r.status_code == 404


def test_patch_empty_body_returns_400(session, owner_token, fresh_viz):
    r = session.patch(
        f"{API}/visualizations/{fresh_viz['id']}",
        json={},
        headers=auth(owner_token),
    )
    assert r.status_code == 400, r.text


def test_patch_other_user_returns_404(session, other_token, fresh_viz):
    r = session.patch(
        f"{API}/visualizations/{fresh_viz['id']}",
        json={"published": False},
        headers=auth(other_token),
    )
    assert r.status_code == 404


def test_patch_unpublish_as_owner(session, owner_token, fresh_viz):
    r = session.patch(
        f"{API}/visualizations/{fresh_viz['id']}",
        json={"published": False},
        headers=auth(owner_token),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == fresh_viz["id"]
    assert body.get("published") is False
    assert "_id" not in body


def test_showroom_excludes_unpublished(session, fresh_viz):
    # fresh_viz was just unpublished in prior test
    r = session.get(f"{API}/public/stones/{STONE_ID}")
    assert r.status_code == 200
    ids = [x["id"] for x in r.json().get("renders", [])]
    assert fresh_viz["id"] not in ids, f"unpublished viz appears in showroom: {ids}"


def test_patch_republish_as_owner(session, owner_token, fresh_viz):
    r = session.patch(
        f"{API}/visualizations/{fresh_viz['id']}",
        json={"published": True},
        headers=auth(owner_token),
    )
    assert r.status_code == 200, r.text
    assert r.json().get("published") is True


def test_showroom_includes_republished(session, fresh_viz):
    # Assuming this stone has <= 8 total renders, the just-republished one should
    # appear in the latest-8 showroom window. If it doesn't appear, we at minimum
    # assert that the showroom DID NOT return it while it was unpublished above.
    r = session.get(f"{API}/public/stones/{STONE_ID}")
    assert r.status_code == 200
    data = r.json()
    renders = data.get("renders", [])
    # Hard cap of 8
    assert len(renders) <= 8
    ids = [x["id"] for x in renders]
    # Newly-republished viz is the most recently created on this stone in this run,
    # so it should be present (created_at sort desc, limit 8).
    assert fresh_viz["id"] in ids, (
        f"Expected republished viz in showroom; got {ids}. If this stone has "
        ">8 renders already, this assertion is acceptable to soften."
    )


# Showroom cap & empty-safe ---------------------------------------------------
def test_showroom_cap_is_8(session):
    r = session.get(f"{API}/public/stones/{STONE_ID}")
    assert r.status_code == 200
    assert len(r.json().get("renders", [])) <= 8


def test_showroom_empty_safe_for_stone_with_no_renders(session, admin_token_fixture):
    # Create a brand-new active stone, query its showroom — should be 200 with [].
    new_name = f"It4 Empty {uuid.uuid4().hex[:6]}"
    create = session.post(
        f"{API}/admin/stones",
        json={
            "name": new_name,
            "type": "Quartz",
            "finish": "Polished",
            "image_url": "https://example.com/x.jpg",
        },
        headers=auth(admin_token_fixture),
    )
    assert create.status_code == 200, create.text
    sid = create.json()["id"]
    try:
        r = session.get(f"{API}/public/stones/{sid}")
        assert r.status_code == 200
        assert r.json().get("renders") == []
    finally:
        session.delete(f"{API}/admin/stones/{sid}", headers=auth(admin_token_fixture))


@pytest.fixture(scope="module")
def admin_token_fixture(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200
    return r.json()["access_token"]


# Auth gate on PATCH ----------------------------------------------------------
def test_patch_requires_auth(session, fresh_viz):
    r = session.patch(
        f"{API}/visualizations/{fresh_viz['id']}",
        json={"published": True},
    )
    assert r.status_code == 401
