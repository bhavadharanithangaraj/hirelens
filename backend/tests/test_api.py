import pytest

from tests.conftest import JD, RESUME


def analyze(client, resume=RESUME, jd=JD):
    return client.post("/api/analyze", json={"resume_text": resume, "jd_text": jd})


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_analyze_returns_full_result(client):
    response = analyze(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert "Developer" in body["role_title"]
    assert 0 <= body["match_score"] <= 100
    assert {"React", "TypeScript", "Python", "FastAPI"} <= set(body["matched_skills"])
    assert {"AWS", "Kubernetes", "RAG"} <= set(body["missing_skills"])
    assert "LangChain" in body["nice_to_have_skills"]
    assert body["strengths"] and body["summary"]
    assert 3 <= len(body["bullets"]) <= 5
    assert all(b["original"] and b["improved"] and b["reason"] for b in body["bullets"])


@pytest.mark.parametrize(
    "payload",
    [
        {"resume_text": "too short", "jd_text": JD},
        {"resume_text": RESUME, "jd_text": "   short   "},
        {"resume_text": RESUME},
    ],
)
def test_analyze_validation_error(client, payload):
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 422


def test_history_list_and_detail(client):
    first = analyze(client).json()
    second = analyze(client).json()

    listing = client.get("/api/history")
    assert listing.status_code == 200
    items = listing.json()
    assert [item["id"] for item in items] == [second["id"], first["id"]]  # newest first
    assert set(items[0]) == {"id", "role_title", "match_score", "created_at"}

    detail = client.get(f"/api/history/{first['id']}")
    assert detail.status_code == 200
    assert detail.json() == first


def test_history_detail_not_found(client):
    assert client.get("/api/history/9999").status_code == 404
