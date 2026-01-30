"""Vector search and embedding endpoints."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config.database import get_db
from app.services.semantic_search_service import SemanticSearchService
from app.services.vector_store import get_vector_store
from app.schemas.vector_search import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    GenerateEmbeddingsRequest,
    GenerateEmbeddingsResponse
)

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search over document chunks.
    
    - **query**: Search query text
    - **top_k**: Number of results to return (optional)
    - **file_id**: Optional file ID to filter results
    
    Returns relevant chunks ranked by similarity.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query text is required")
    
    try:
        results = await SemanticSearchService.search(
            query_text=request.query,
            db=db,
            top_k=request.top_k,
            file_id=request.file_id
        )
        
        return SearchResponse(
            query=request.query,
            results=[
                SearchResult(
                    chunk_id=r["chunk_id"],
                    file_id=r["file_id"],
                    chunk_index=r["chunk_index"],
                    text=r["text"],
                    score=r["score"],
                    distance=r["distance"],
                    char_count=r["char_count"],
                    page_number=r.get("page_number")
                )
                for r in results
            ],
            total_results=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/files/{file_id}/embeddings", response_model=GenerateEmbeddingsResponse, status_code=201)
async def generate_embeddings_for_file(
    file_id: int,
    request: Optional[GenerateEmbeddingsRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate embeddings for all chunks of a file.
    
    - **file_id**: ID of the file
    - **model**: Optional embedding model to use
    
    Creates embeddings and adds them to the vector store.
    """
    try:
        count = await SemanticSearchService.generate_embeddings_for_file(
            file_id=file_id,
            db=db,
            model=request.model if request else None
        )
        
        return GenerateEmbeddingsResponse(
            embeddings_created=count,
            message=f"Generated {count} embeddings successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/chunks/embeddings", response_model=GenerateEmbeddingsResponse, status_code=201)
async def generate_embeddings_for_chunks(
    request: GenerateEmbeddingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate embeddings for specific chunks.
    
    - **chunk_ids**: List of chunk IDs to process
    - **model**: Optional embedding model to use
    """
    if not request.chunk_ids:
        raise HTTPException(status_code=400, detail="chunk_ids is required")
    
    try:
        embeddings = await SemanticSearchService.generate_embeddings_for_chunks(
            chunk_ids=request.chunk_ids,
            db=db,
            model=request.model
        )
        
        return GenerateEmbeddingsResponse(
            embeddings_created=len(embeddings),
            message=f"Generated {len(embeddings)} embeddings successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@router.post("/vector-store/rebuild", status_code=200)
async def rebuild_vector_store(
    db: AsyncSession = Depends(get_db)
):
    """
    Rebuild the FAISS vector store index from all embeddings in the database.
    
    Useful after bulk updates or when the index becomes out of sync.
    """
    try:
        vector_store = get_vector_store()
        await vector_store.build_index(db)
        
        return {
            "message": "Vector store rebuilt successfully",
            "index_size": vector_store.index.ntotal if vector_store.index else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rebuild vector store: {str(e)}")


@router.get("/vector-store/status", status_code=200)
async def get_vector_store_status():
    """
    Get status of the vector store.
    
    Returns information about the current index state.
    """
    try:
        vector_store = get_vector_store()
        
        return {
            "index_loaded": vector_store.index is not None,
            "index_size": vector_store.index.ntotal if vector_store.index else 0,
            "dimension": vector_store.dimension,
            "index_path": str(vector_store.index_path)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vector store status: {str(e)}")

