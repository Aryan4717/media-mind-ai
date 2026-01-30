import pytest

from app.models.file import FileMetadata, FileType


@pytest.mark.asyncio
async def test_media_playback_endpoint(client, session_maker):
    async with session_maker() as db:
        f = FileMetadata(
            filename="video.mp4",
            original_filename="video.mp4",
            file_type=FileType.VIDEO,
            file_path="uploads/video/video.mp4",
            file_size=123,
            file_size_mb=123 / (1024 * 1024),  # Convert bytes to MB
            mime_type="video/mp4",
        )
        db.add(f)
        await db.commit()
        await db.refresh(f)

        file_id = f.id

    r = await client.get(f"/api/v1/files/{file_id}/playback", params={"timestamp": 10.5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["file_id"] == file_id
    assert data["timestamp"] == 10.5
    assert data["file_url"].endswith(f"/api/v1/files/{file_id}/download")


