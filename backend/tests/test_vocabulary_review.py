from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.vocabulary import VocabularyEntry


def test_new_entries_are_immediately_due_for_review(client: TestClient) -> None:
    collection = client.post("/api/v1/collections", json={"name": "The Alchemist"}).json()
    client.post("/api/v1/vocabulary", json={"collection_id": collection["id"], "term": "omen"})

    response = client.get("/api/v1/vocabulary/review/due")

    assert response.status_code == 200
    assert any(entry["term"] == "omen" for entry in response.json())


def test_grading_good_pushes_the_entry_out_of_the_due_queue(client: TestClient) -> None:
    collection = client.post("/api/v1/collections", json={"name": "The Alchemist"}).json()
    entry = client.post(
        "/api/v1/vocabulary", json={"collection_id": collection["id"], "term": "omen"}
    ).json()

    review = client.post(f"/api/v1/vocabulary/{entry['id']}/review", json={"result": "good"})

    assert review.status_code == 200
    assert review.json()["review_interval_days"] >= 1
    due_terms = [item["term"] for item in client.get("/api/v1/vocabulary/review/due").json()]
    assert "omen" not in due_terms


def test_review_is_scoped_to_the_authenticated_user(
    client: TestClient, current_user: dict[str, str]
) -> None:
    collection = client.post("/api/v1/collections", json={"name": "Private"}).json()
    entry = client.post(
        "/api/v1/vocabulary", json={"collection_id": collection["id"], "term": "omen"}
    ).json()

    current_user["id"] = "user-b"
    response = client.post(f"/api/v1/vocabulary/{entry['id']}/review", json={"result": "good"})

    assert response.status_code == 404


def test_overdue_entry_becomes_due_again(client: TestClient, session: Session) -> None:
    collection = client.post("/api/v1/collections", json={"name": "The Alchemist"}).json()
    entry_id = client.post(
        "/api/v1/vocabulary", json={"collection_id": collection["id"], "term": "omen"}
    ).json()["id"]

    stored = session.get(VocabularyEntry, entry_id)
    stored.review_due_at = datetime.utcnow() + timedelta(days=30)
    session.add(stored)
    session.commit()

    assert "omen" not in [item["term"] for item in client.get("/api/v1/vocabulary/review/due").json()]

    stored.review_due_at = datetime.utcnow() - timedelta(minutes=1)
    session.add(stored)
    session.commit()

    assert "omen" in [item["term"] for item in client.get("/api/v1/vocabulary/review/due").json()]
