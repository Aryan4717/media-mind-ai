"""Q&A chatbot endpoints using RAG."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.config.database import get_db
from app.services.rag_service import RAGService
from app.schemas.qa import QuestionRequest, AnswerResponse, SourceInfo

router = APIRouter()


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question and get an answer using RAG (Retrieval-Augmented Generation).
    
    - **question**: The question to ask
    - **file_id**: Optional file ID to limit search to specific file
    - **top_k**: Number of chunks to retrieve (optional)
    - **model**: LLM model to use (optional)
    - **temperature**: Temperature for LLM generation (optional)
    
    Returns an answer based only on the uploaded document content.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = await RAGService.answer_question(
            question=request.question,
            db=db,
            top_k=request.top_k,
            file_id=request.file_id,
            model=request.model,
            temperature=request.temperature
        )
        
        return AnswerResponse(
            answer=result["answer"],
            sources=[
                SourceInfo(
                    chunk_id=s["chunk_id"],
                    file_id=s["file_id"],
                    chunk_index=s["chunk_index"],
                    text_preview=s["text_preview"],
                    score=s["score"],
                    page_number=s.get("page_number")
                )
                for s in result["sources"]
            ],
            confidence=result["confidence"],
            chunks_used=result["chunks_used"],
            model=result["model"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@router.post("/ask/stream")
async def ask_question_streaming(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question and get a streaming answer using RAG.
    
    Returns a streaming response with answer chunks and sources.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    async def generate_stream():
        try:
            async for chunk in RAGService.answer_question_with_streaming(
                question=request.question,
                db=db,
                top_k=request.top_k,
                file_id=request.file_id,
                model=request.model,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            error_chunk = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/files/{file_id}/ask", response_model=AnswerResponse)
async def ask_question_about_file(
    file_id: int,
    request: QuestionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question about a specific file using RAG.
    
    - **file_id**: ID of the file to query
    - **question**: The question to ask
    - **top_k**: Number of chunks to retrieve (optional)
    - **model**: LLM model to use (optional)
    - **temperature**: Temperature for LLM generation (optional)
    
    Returns an answer based only on the specified file's content.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = await RAGService.answer_question(
            question=request.question,
            db=db,
            top_k=request.top_k,
            file_id=file_id,  # Override with path parameter
            model=request.model,
            temperature=request.temperature
        )
        
        return AnswerResponse(
            answer=result["answer"],
            sources=[
                SourceInfo(
                    chunk_id=s["chunk_id"],
                    file_id=s["file_id"],
                    chunk_index=s["chunk_index"],
                    text_preview=s["text_preview"],
                    score=s["score"],
                    page_number=s.get("page_number")
                )
                for s in result["sources"]
            ],
            confidence=result["confidence"],
            chunks_used=result["chunks_used"],
            model=result["model"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

