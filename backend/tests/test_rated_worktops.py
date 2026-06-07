"""Backend integration tests for Rated Worktops."""
import os
import uuid
import base64
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE_URL:
    # Read from frontend/.env
    fe = Path("/app/frontend/.env").read_text()
    for line in fe.splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@ratedworktops.com"
ADMIN_PASS = "Admin@RW2026"

# 1x1 valid JPEG (base64) used as the "kitchen" image
TINY_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA//"
    "2Q=="
)


@pytest.fixture(scope="session")
def session():
    return requests.Session()


@pytest.fixture(scope="session")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def new_user(session):
    email = f"test_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(f"{API}/auth/register", json={"email": email, "password": "Test@1234", "name": "Test User"})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["user"]["credits"] == 3
    assert data["access_token"]
    return {"email": email, "token": data["access_token"], "id": data["user"]["id"]}


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ---------- AUTH ----------
def test_health(session):
    r = session.get(f"{API}/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_admin_login(admin_token):
    assert admin_token and len(admin_token) > 20


def test_register_returns_credits(new_user):
    assert new_user["token"]


def test_login_after_register(session, new_user):
    r = session.post(f"{API}/auth/login", json={"email": new_user["email"], "password": "Test@1234"})
    assert r.status_code == 200
    assert r.json()["user"]["credits"] == 3


def test_login_invalid(session):
    r = session.post(f"{API}/auth/login", json={"email": "nope@nope.com", "password": "wrong"})
    assert r.status_code == 401


def test_me(session, new_user):
    r = session.get(f"{API}/auth/me", headers=auth(new_user["token"]))
    assert r.status_code == 200
    assert r.json()["email"] == new_user["email"]


def test_me_unauthed(session):
    r = session.get(f"{API}/auth/me")
    assert r.status_code == 401


# ---------- STONES ----------
def test_list_stones(session, new_user):
    r = session.get(f"{API}/stones", headers=auth(new_user["token"]))
    assert r.status_code == 200
    data = r.json()
    assert len(data["catalog"]) == 12
    assert any(s["id"] == "carrara-white" for s in data["catalog"])
    assert isinstance(data["custom"], list)


def test_add_custom_stone(session, new_user):
    body = {
        "name": "TEST_CustomMarble",
        "type": "Marble",
        "finish": "Polished",
        "image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
    }
    r = session.post(f"{API}/stones/custom", json=body, headers=auth(new_user["token"]))
    assert r.status_code == 200
    data = r.json()
    assert data["id"].startswith("custom-")
    assert data["is_custom"] is True
    # verify it shows in list
    r2 = session.get(f"{API}/stones", headers=auth(new_user["token"]))
    assert any(c["id"] == data["id"] for c in r2.json()["custom"])


# ---------- CREDITS ----------
def test_credits_endpoint(session, new_user):
    r = session.get(f"{API}/credits", headers=auth(new_user["token"]))
    assert r.status_code == 200
    data = r.json()
    assert data["balance"] == 3
    assert len(data["packs"]) == 3
    assert {p["id"] for p in data["packs"]} == {"starter", "pro", "studio"}


def test_purchase_credits_starter(session, new_user):
    # Iteration 2: stripe removed, only paypal/apple_pay/google_pay accepted (all mocked)
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "starter", "method": "paypal"},
        headers=auth(new_user["token"]),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["mocked"] is True
    assert data["balance"] >= 13  # 3 free + 10 starter
    assert data["transaction"]["credits"] == 10


def test_purchase_invalid_pack(session, new_user):
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "nope", "method": "paypal"},
        headers=auth(new_user["token"]),
    )
    assert r.status_code == 400


def test_purchase_invalid_method(session, new_user):
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "starter", "method": "bitcoin"},
        headers=auth(new_user["token"]),
    )
    assert r.status_code == 400


# ---------- VISUALIZE (core) ----------
def test_visualize_core(session, new_user):
    # use admin token has 9999 credits; but spec says verify decrement on a user.
    # Use new_user (now has 13 credits after starter purchase ran earlier in suite).
    r = session.get(f"{API}/credits", headers=auth(new_user["token"]))
    pre_balance = r.json()["balance"]

    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": "carrara-white",
        "mode": "auto",
        "instructions": "",
    }
    r = session.post(f"{API}/visualize", json=payload, headers=auth(new_user["token"]), timeout=120)
    assert r.status_code == 200, f"visualize failed {r.status_code}: {r.text[:400]}"
    data = r.json()
    assert "visualization" in data
    assert data["visualization"]["result_image"].startswith("data:image/")
    assert data["credits_remaining"] == pre_balance - 1


def test_visualizations_list(session, new_user):
    r = session.get(f"{API}/visualizations", headers=auth(new_user["token"]))
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1


def test_visualize_no_credits(session):
    # Register a brand-new user (3 free credits), drain them with 3 visualize calls, then expect 402 on the 4th.
    email = f"drain_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(f"{API}/auth/register", json={"email": email, "password": "Test@1234", "name": "Drain"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": "carrara-white",
        "mode": "auto",
    }
    for i in range(3):
        rr = session.post(f"{API}/visualize", json=payload, headers=auth(token), timeout=120)
        assert rr.status_code == 200, f"call {i} failed: {rr.status_code} {rr.text[:200]}"
    # Now credits == 0
    rr = session.post(f"{API}/visualize", json=payload, headers=auth(token), timeout=30)
    assert rr.status_code == 402


def test_visualize_stone_not_found(session, new_user):
    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": "does-not-exist",
        "mode": "auto",
    }
    r = session.post(f"{API}/visualize", json=payload, headers=auth(new_user["token"]))
    assert r.status_code == 404
