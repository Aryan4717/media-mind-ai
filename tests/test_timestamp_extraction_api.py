import pytest

from app.models.file import FileMetadata, FileType
from app.models.transcription import Transcription


@pytest.mark.asyncio
async def test_timestamp_extraction_endpoint(client, session_maker):
    # Seed audio file + completed transcription with segments
    async with session_maker() as db:
        f = FileMetadata(
            filename="audio.mp3",
            original_filename="audio.mp3",
            file_type=FileType.AUDIO,
            file_path="uploads/audio/audio.mp3",
            file_size=123,
            file_size_mb=123 / (1024 * 1024),  # Convert bytes to MB
            mime_type="audio/mpeg",
        )
        db.add(f)
        await db.flush()

        t = Transcription(
            file_id=f.id,
            full_text="Machine learning is discussed here.",
            language="en",
            duration=120.0,
            status="completed",
            segments=[
                {"start": 10.0, "end": 12.0, "text": "Machine learning is great."},
                {"start": 50.0, "end": 55.0, "text": "Something else."},
            ],
        )
        db.add(t)
        await db.commit()

        file_id = f.id

    r = await client.post(f"/api/v1/files/{file_id}/timestamps", json={"text": "machine learning"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["file_id"] == file_id
    assert data["total_segments"] >= 1
    assert any(ts["start"] == 10.0 for ts in data["timestamps"])


