"""
Semantic Matching using Vector Embeddings
Uses Groq/OpenAI-compatible embeddings to compute semantic similarity
"""
import numpy as np
from typing import List, Tuple
from groq import Groq
from core.config import settings
from core.logging_config import get_logger
from core.throttle import groq_throttle

logger = get_logger("embeddings")


def get_client() -> Groq:
    return Groq(api_key=settings.GROQ_API_KEY)


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.
    Returns a value between 0 and 1 (0 = completely different, 1 = identical)
    """
    if not vec1 or not vec2:
        return 0.0
    
    # Convert to numpy arrays
    a = np.array(vec1)
    b = np.array(vec2)
    
    # Compute cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    similarity = dot_product / (norm_a * norm_b)
    
    # Clamp between 0 and 1
    return max(0.0, min(1.0, float(similarity)))


@groq_throttle
async def generate_embedding(text: str, model: str = "text-embedding-ada-002") -> List[float]:
    """
    Generate embedding vector for text using OpenAI-compatible API.
    
    Note: Groq doesn't directly support embeddings yet, so this uses
    a fallback approach with text chunking and LLM-based feature extraction.
    For production, you'd use OpenAI's embedding API or similar.
    """
    logger.debug(f"Generating semantic embedding for text ({len(text)} chars)")
    # Truncate text to avoid token limits
    text = text[:8000]
    
    # For now, we'll use a simplified approach:
    # Generate a "semantic fingerprint" using Groq LLM to extract key concepts
    # In production, use proper embedding models (OpenAI, Cohere, etc.)
    
    try:
        client = get_client()
        
        # Use LLM to extract semantic features (simplified embedding approach)
        prompt = f"""Extract the key semantic concepts from this text as a list of weighted features.
Focus on: skills, experience level, domain expertise, responsibilities, technologies.

Text: {text[:3000]}

Return ONLY a JSON array of 20 semantic features with weights 0-1:
{{"features": [{{"concept": "python", "weight": 0.9}}, {{"concept": "senior", "weight": 0.8}}]}}"""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512,
        )
        
        raw = response.choices[0].message.content or ""
        
        # Parse the semantic features
        import json
        import re
        
        # Extract JSON
        raw = re.sub(r"```(?:json)?", "", raw).strip("` \n")
        try:
            data = json.loads(raw)
        except:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                data = json.loads(match.group(0))
            else:
                logger.warning("Failed to parse embedding response, returning zero vector")
                return [0.0] * 128  # Return zero vector on error
        
        features = data.get("features", [])
        
        # Convert to fixed-size vector (128 dimensions)
        # Use a simple hash-based approach for concept -> dimension mapping
        vector = [0.0] * 128
        for f in features[:20]:
            concept = str(f.get("concept", "")).lower()
            weight = float(f.get("weight", 0.5))
            
            # Hash concept to dimension index
            hash_val = hash(concept)
            idx = hash_val % 128
            vector[idx] = max(vector[idx], weight)  # Take max if collision
        
        logger.info(f"✅ Generated semantic embedding (simplified approach, {len(features)} features)")
        return vector
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {type(e).__name__}: {e}")
        # Return zero vector on error
        return [0.0] * 128


async def compute_semantic_similarity(resume_text: str, jd_text: str) -> Tuple[float, dict]:
    """
    Compute semantic similarity between resume and job description.
    
    Returns:
        - similarity score (0-100)
        - metadata dict with additional info
    """
    logger.info("Computing semantic similarity between resume and JD")
    try:
        # Generate embeddings for both texts
        resume_embedding = await generate_embedding(resume_text)
        jd_embedding = await generate_embedding(jd_text)
        
        # Compute cosine similarity
        raw_similarity = compute_cosine_similarity(resume_embedding, jd_embedding)
        
        # Scale to 0-100
        score = round(raw_similarity * 100, 1)
        
        metadata = {
            "embedding_dimensions": len(resume_embedding),
            "raw_similarity": round(raw_similarity, 4),
            "interpretation": _interpret_score(score),
        }
        
        logger.info(f"✅ Semantic similarity computed: {score}% (interpretation: {metadata['interpretation'][:50]}...)")
        return score, metadata
    except Exception as e:
        logger.error(f"Semantic similarity computation failed: {type(e).__name__}: {e}")
        # Return fallback score
        return 50.0, {
            "embedding_dimensions": 128,
            "raw_similarity": 0.5,
            "interpretation": "Unable to compute semantic similarity at this time",
        }


def _interpret_score(score: float) -> str:
    """Interpret semantic similarity score for users."""
    if score >= 85:
        return "Excellent semantic match — your resume deeply aligns with this role's requirements"
    elif score >= 70:
        return "Strong semantic match — good alignment with the role's core needs"
    elif score >= 55:
        return "Moderate semantic match — some conceptual alignment, but gaps exist"
    elif score >= 40:
        return "Weak semantic match — limited conceptual overlap with the role"
    else:
        return "Poor semantic match — fundamentally different focus areas"
