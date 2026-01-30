import pytest


@pytest.mark.asyncio
async def test_upload_list_download_delete_roundtrip(client, uploads_dir):
    # Upload a small PDF-like payload
    content = b"%PDF-1.4\n%test\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
    files = {"file": ("test.pdf", content, "application/pdf")}

    r = await client.post("/api/v1/files/upload", files=files)
    assert r.status_code == 201, r.text
    file_id = r.json()["id"]

    # List
    r = await client.get("/api/v1/files/list")
    assert r.status_code == 200
    payload = r.json()
    assert any(f["id"] == file_id for f in payload["files"])

    # Metadata
    r = await client.get(f"/api/v1/files/{file_id}")
    assert r.status_code == 200
    assert r.json()["id"] == file_id

    # Download should return bytes
    r = await client.get(f"/api/v1/files/{file_id}/download")
    assert r.status_code == 200
    assert r.content == content

    # Delete
    r = await client.delete(f"/api/v1/files/{file_id}")
    assert r.status_code == 204  # No Content is standard for DELETE

    # Ensure it is gone
    r = await client.get(f"/api/v1/files/{file_id}")
    assert r.status_code == 404
