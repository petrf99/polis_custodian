import uuid
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import psycopg2
from typing import Optional

import os
from datetime import datetime

import json

from logging import getLogger
logger = getLogger(__name__)

# === Config ===
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "intfloat/multilingual-e5-base")
QDRANT_URL = os.getenv("QDRANT_HOST", "http://localhost:6333")
SAGE_CACHE_COLLECTION = os.getenv("SAGE_CACHE_COLLECTION", "sage_cache")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# === Init ===
model = SentenceTransformer(EMBED_MODEL_NAME)
qdrant = QdrantClient(QDRANT_URL)
SAGE_CACHE_THRESHOLD = float(os.getenv("SAGE_CACHE_THRESHOLD", 0.85))

# === Functions ===

def embed_question(text: str) -> list[float]:
    formatted = f"query: {text.strip()}"
    return model.encode([formatted], show_progress_bar=False)[0].tolist()




def search_similar_vectors(vector: list[float], top_k: int = 1, collection_name: str = 'sage_cache') -> Optional[dict]:
    """Search in qdant for similar questions above threshold."""

    results = qdrant.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=top_k,
        with_payload=True
    )

    points = []
    for point in results:
        if collection_name == 'sage_cache' and point.score < SAGE_CACHE_THRESHOLD:
            pass
        points.append({
                "payload": point.payload,
                "score": point.score
            })
    
    return points



def upsert_to_sage_cache(vector: list[float], data, context, context_score, answered):
    logger.info("[UPSERTING QUESTION TO QDRANT CACHE]")
    question_id = data['question_id'] or str(uuid.uuid4())

    payload = {
        "question_id": question_id,
        "timestamp": datetime.now().isoformat()
    }

    point = PointStruct(id=question_id, vector=vector, payload=payload)

    qdrant.upsert(
        collection_name=SAGE_CACHE_COLLECTION,
        points=[point]
    )
    
    logger.info('[QUESTION INSERTED TO QDRANT CACHE. INSERT TO PSQL]')

    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    logger.info("[INSERT DATA TO PGSQL. CONNECTION ESTABLISHED]")

    psql_cache_insert_query = """
    INSERT INTO sage_questions_cache (
        question_id, 
        speaker, 
        question, 
        context,
        question_dttm,  
        lang,
        answered, 
        context_score, 
        metadata
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    cursor.execute(
            psql_cache_insert_query,
            (
                data['question_id'], 
                '', 
                data['question'],
                context,
                data['question_dttm'], 
                '',
                answered, 
                context_score, 
                json.dumps({'use_cache': data['use_cache'],
                            'search_width': data['search_width'],
                            'search_depth': data['search_depth']})
            )
        )
    
    conn.commit()
    cursor.close()
    conn.close()

    return 0
