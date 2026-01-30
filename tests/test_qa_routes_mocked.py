import pytest

from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_qa_ask_endpoint_mocked(client, monkeypatch):
    async def fake_answer_question(*args, **kwargs):
        return {
            "answer": "mock-answer",
            "sources": [
                {
                    "chunk_id": 1,
                    "file_id": 1,
                    "chunk_index": 0,
                    "text_preview": "preview",
                    "score": 0.9,
                    "page_number": None,
                    "timestamps": [
                        {
                            "start": 10.0,
                            "end": 12.0,
                            "text": "Machine learning",
                            "duration": 2.0,
                            "formatted_start": "00:10.000",
                            "formatted_end": "00:12.000",
                        }
                    ],
                }
            ],
            "confidence": 0.9,
            "chunks_used": 1,
            "model": "mock-model",
            "timestamps": [
                {
                    "start": 10.0,
                    "end": 12.0,
                    "text": "Machine learning",
                    "duration": 2.0,
                    "formatted_start": "00:10.000",
                    "formatted_end": "00:12.000",
                }
            ],
        }

    monkeypatch.setattr(RAGService, "answer_question", fake_answer_question)

    r = await client.post("/api/v1/ask", json={"question": "hi"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["answer"] == "mock-answer"
    assert data["sources"][0]["timestamps"][0]["start"] == 10.0
    assert data["timestamps"][0]["formatted_start"] == "00:10.000"


@pytest.mark.asyncio
async def test_qa_stream_endpoint_mocked(client, monkeypatch):
    async def fake_stream(*args, **kwargs):
        yield {"answer_chunk": "Hello "}
        yield {"answer_chunk": "world"}
        yield {
            "final_response": {
                "answer": "Hello world",
                "sources": [],
                "confidence": 1.0,
                "chunks_used": 0,
                "model": "mock-model",
                "timestamps": [],
            }
        }

    monkeypatch.setattr(RAGService, "answer_question_with_streaming", fake_stream)

    r = await client.post("/api/v1/ask/stream", json={"question": "stream"})
    assert r.status_code == 200
    body = r.text
    assert "answer_chunk" in body
    assert "final_response" in body


