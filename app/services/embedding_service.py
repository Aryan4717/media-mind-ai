"""Service for generating embeddings using OpenAI."""

import logging
from typing import List, Optional
import asyncio

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""
    
    @staticmethod
    async def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model: Embedding model to use (defaults to settings)
        
        Returns:
            List of floats representing the embedding vector
        """
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for embeddings")
        
        model = model or settings.embedding_model
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # OpenAI embeddings API (synchronous, but we'll run in executor)
            response = client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    @staticmethod
    async def generate_embeddings_batch(
        texts: List[str],
        model: Optional[str] = None,
        batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            model: Embedding model to use (defaults to settings)
            batch_size: Batch size for processing (defaults to settings)
        
        Returns:
            List of embedding vectors
        """
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required for embeddings")
        
        model = model or settings.embedding_model
        batch_size = batch_size or settings.embedding_batch_size
        
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.openai_api_key)
            
            # Process in batches
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Generate embeddings for batch
                response = client.embeddings.create(
                    model=model,
                    input=batch
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Small delay to respect rate limits
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
            
            return all_embeddings
        except ImportError:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Error generating embeddings batch: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")

