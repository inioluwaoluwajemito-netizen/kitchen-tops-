"""Iteration 2 tests: featured stones, public render permalink, quotes lead-gen, Google auth error path."""
import os
import uuid
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

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
    email = f"it2_{uuid.uuid4().hex[:8]}@ratedworktops.com"
    r = session.post(f"{API}/auth/register", json={"email": email, "password": "Test@1234", "name": "It2 User"})
    assert r.status_code == 200
    return {"token": r.json()["access_token"], "email": email, "id": r.json()["user"]["id"]}


# =========== PUBLIC STONES + FEATURED ===========
def test_public_stones_returns_all_active(session):
    r = session.get(f"{API}/public/stones")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    # Every item exposes expected fields
    s0 = data["items"][0]
    for k in ["id", "name", "type", "finish", "image_url", "featured"]:
        assert k in s0, f"missing field {k}"


def test_admin_can_set_featured(session, admin_token):
    # Set carrara-white as featured
    r = session.patch(
        f"{API}/admin/stones/carrara-white",
        json={"featured": True},
        headers=auth(admin_token),
    )
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    assert r.json().get("featured") is True


def test_non_admin_cannot_patch_stone(session, user_token):
    r = session.patch(
        f"{API}/admin/stones/carrara-white",
        json={"featured": True},
        headers=auth(user_token["token"]),
    )
    assert r.status_code == 403


def test_public_stones_featured_only(session, admin_token):
    # Ensure at least one stone featured
    session.patch(
        f"{API}/admin/stones/carrara-white",
        json={"featured": True},
        headers=auth(admin_token),
    )
    r = session.get(f"{API}/public/stones", params={"featured_only": "true"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert all(s["featured"] is True for s in items)
    assert any(s["id"] == "carrara-white" for s in items)


def test_admin_can_unset_featured(session, admin_token):
    r = session.patch(
        f"{API}/admin/stones/carrara-white",
        json={"featured": False},
        headers=auth(admin_token),
    )
    assert r.status_code == 200
    assert r.json().get("featured") is False
    # re-set to true so other tests are stable
    session.patch(
        f"{API}/admin/stones/carrara-white",
        json={"featured": True},
        headers=auth(admin_token),
    )


# =========== PUBLIC RENDER PERMALINK ===========
@pytest.fixture(scope="module")
def visualization_id(session, user_token):
    """Create a real visualization via Gemini (regression test for end-to-end pipeline)."""
    payload = {
        "kitchen_image_base64": f"data:image/jpeg;base64,{TINY_JPEG_B64}",
        "stone_id": "carrara-white",
        "mode": "auto",
        "instructions": "",
    }
    r = session.post(f"{API}/visualize", json=payload, headers=auth(user_token["token"]), timeout=120)
    assert r.status_code == 200, f"visualize failed: {r.status_code} {r.text[:300]}"
    viz = r.json()["visualization"]
    # Iteration 3: result_image is now a backend URL path, not a data: URL.
    # Accept either for backward-compat during transition.
    assert viz["result_image"].startswith(("data:image/", "/api/public/renders/"))
    return viz["id"]


def test_public_render_returns_200_no_auth(session, visualization_id):
    r = session.get(f"{API}/public/renders/{visualization_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == visualization_id
    assert data["stone_name"]
    assert data["result_image"].startswith(("data:image/", "/api/public/renders/"))


def test_public_render_returns_404_bogus(session):
    r = session.get(f"{API}/public/renders/bogus-id-{uuid.uuid4().hex}")
    assert r.status_code == 404


# =========== QUOTES — public POST ===========
@pytest.fixture(scope="module")
def created_quote_basic(session):
    body = {
        "name": "TEST_Jane Doe",
        "email": "jane.doe@example.com",
        "phone": "+44 7700 900123",
        "notes": "I'd like a quote for this stone",
        "stone_id": "carrara-white",
    }
    r = session.post(f"{API}/quotes", json=body)  # NO AUTH
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "received"
    assert data["id"]
    return {"id": data["id"], "payload": body}


def test_create_quote_no_auth(created_quote_basic):
    assert created_quote_basic["id"]


def test_quote_with_visualization_pulls_stone(session, visualization_id):
    body = {
        "name": "TEST_Vis Linked",
        "email": "vis.linked@example.com",
        "phone": "",
        "notes": "From a render",
        "visualization_id": visualization_id,
    }
    r = session.post(f"{API}/quotes", json=body)
    assert r.status_code == 200
    quote_id = r.json()["id"]

    # Admin fetches and verifies stone context was pulled
    admin_login = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    tok = admin_login.json()["access_token"]
    r2 = session.get(f"{API}/admin/quotes", headers=auth(tok))
    assert r2.status_code == 200
    items = r2.json()["items"]
    match = next((q for q in items if q["id"] == quote_id), None)
    assert match is not None, "quote not found in admin list"
    assert match.get("stone_id") == "carrara-white"
    assert match.get("visualization") is not None
    assert match["visualization"].get("stone_id") == "carrara-white"
    assert match.get("stone", {}).get("name")  # stone_name populated


# =========== ADMIN QUOTES list/filter/update/delete ===========
def test_admin_list_quotes(session, admin_token, created_quote_basic):
    r = session.get(f"{API}/admin/quotes", headers=auth(admin_token))
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "counts" in data
    assert isinstance(data["counts"], dict)
    assert data["counts"].get("new", 0) >= 1
    # verify our quote present and stored
    qid = created_quote_basic["id"]
    found = next((q for q in data["items"] if q["id"] == qid), None)
    assert found is not None
    assert found["name"] == created_quote_basic["payload"]["name"]
    assert found["email"] == created_quote_basic["payload"]["email"]
    assert found["phone"] == created_quote_basic["payload"]["phone"]
    assert found["status"] == "new"


def test_admin_quotes_status_filter(session, admin_token):
    r = session.get(f"{API}/admin/quotes", params={"status": "new"}, headers=auth(admin_token))
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(q["status"] == "new" for q in items)


def test_non_admin_cannot_list_quotes(session, user_token):
    r = session.get(f"{API}/admin/quotes", headers=auth(user_token["token"]))
    assert r.status_code == 403


def test_admin_patch_quote_status(session, admin_token, created_quote_basic):
    qid = created_quote_basic["id"]
    r = session.patch(
        f"{API}/admin/quotes/{qid}",
        json={"status": "contacted"},
        headers=auth(admin_token),
    )
    assert r.status_code == 200, f"{r.status_code} {r.text}"
    assert r.json()["status"] == "contacted"


def test_admin_patch_quote_invalid_status(session, admin_token, created_quote_basic):
    qid = created_quote_basic["id"]
    r = session.patch(
        f"{API}/admin/quotes/{qid}",
        json={"status": "wibble"},
        headers=auth(admin_token),
    )
    assert r.status_code == 400


def test_admin_delete_quote(session, admin_token):
    # create a fresh quote then delete it
    cr = session.post(f"{API}/quotes", json={
        "name": "TEST_ToDelete", "email": "del@example.com",
    })
    qid = cr.json()["id"]
    r = session.delete(f"{API}/admin/quotes/{qid}", headers=auth(admin_token))
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    # re-delete -> 404
    r2 = session.delete(f"{API}/admin/quotes/{qid}", headers=auth(admin_token))
    assert r2.status_code == 404


# =========== GOOGLE AUTH error path ===========
def test_google_auth_bogus_session(session):
    r = session.post(f"{API}/auth/google", json={"session_id": "definitely-not-a-real-session-id-xxxx"})
    assert r.status_code == 401, f"expected 401, got {r.status_code} {r.text}"


def test_google_auth_missing_session(session):
    r = session.post(f"{API}/auth/google", json={"session_id": "short"})
    assert r.status_code == 400


# =========== Regression: credits/purchase mocked payments ===========
def test_purchase_paypal_succeeds(session, user_token):
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "starter", "method": "paypal"},
        headers=auth(user_token["token"]),
    )
    assert r.status_code == 200
    assert r.json()["mocked"] is True


def test_purchase_stripe_returns_400(session, user_token):
    r = session.post(
        f"{API}/credits/purchase",
        json={"pack_id": "starter", "method": "stripe"},
        headers=auth(user_token["token"]),
    )
    assert r.status_code == 400
