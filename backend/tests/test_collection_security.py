from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.collection import Collection
from app.models.vocabulary import VocabularyEntry


def test_user_cannot_access_or_delete_another_users_collection(
    client: TestClient,
    current_user: dict[str, str],
) -> None:
    created = client.post("/api/v1/collections", json={"name": "Private Notes"})
    collection_id = created.json()["id"]

    current_user["id"] = "user-b"

    assert client.get(f"/api/v1/collections/{collection_id}").status_code == 404
    assert client.request(
        "DELETE",
        f"/api/v1/collections/{collection_id}",
        json={"confirm": True},
    ).status_code == 404
    assert client.get("/api/v1/collections").json() == []

    current_user["id"] = "user-a"
    assert client.get(f"/api/v1/collections/{collection_id}").status_code == 200


def test_collection_delete_requires_confirmation_and_removes_entries(
    client: TestClient,
    session: Session,
) -> None:
    collection_response = client.post("/api/v1/collections", json={"name": "The Alchemist"})
    collection_id = collection_response.json()["id"]
    entry_response = client.post(
        "/api/v1/vocabulary",
        json={"collection_id": collection_id, "term": "omen"},
    )
    entry_id = entry_response.json()["id"]

    rejected = client.request(
        "DELETE",
        f"/api/v1/collections/{collection_id}",
        json={"confirm": False},
    )

    assert rejected.status_code == 400
    assert rejected.json()["detail"]["error_code"] == "CONFIRMATION_REQUIRED"
    assert session.get(Collection, collection_id) is not None
    assert session.get(VocabularyEntry, entry_id) is not None

    deleted = client.request(
        "DELETE",
        f"/api/v1/collections/{collection_id}",
        json={"confirm": True},
    )

    assert deleted.status_code == 200
    assert session.get(Collection, collection_id) is None
    assert session.get(VocabularyEntry, entry_id) is None