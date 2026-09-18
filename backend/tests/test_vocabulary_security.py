from fastapi.testclient import TestClient


def test_user_cannot_list_or_delete_another_users_vocabulary(
    client: TestClient,
    current_user: dict[str, str],
) -> None:
    collection_response = client.post("/api/v1/collections", json={"name": "Mythos"})
    collection_id = collection_response.json()["id"]
    entry_response = client.post(
        "/api/v1/vocabulary",
        json={"collection_id": collection_id, "term": "hubris"},
    )
    entry_id = entry_response.json()["id"]

    current_user["id"] = "user-b"

    assert client.get(
        "/api/v1/vocabulary",
        params={"collection_id": collection_id},
    ).status_code == 404
    assert client.delete(f"/api/v1/vocabulary/{entry_id}").status_code == 404

    current_user["id"] = "user-a"
    assert client.delete(f"/api/v1/vocabulary/{entry_id}").status_code == 200