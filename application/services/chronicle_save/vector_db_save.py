from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
import psycopg2
import os

# --- Конфиг ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
POSTGRES_CONN = os.getenv("POSTGRES_URL")

COLLECTION_NAME = "utterances"
VECTOR_SIZE = 768  # зависит от модели
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "intfloat/multilingual-e5-base")

# --- Модель и клиенты ---
model = SentenceTransformer(EMBED_MODEL_NAME)
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
pg_conn = psycopg2.connect(POSTGRES_CONN)

def ensure_collection():
    if COLLECTION_NAME not in [col.name for col in qdrant.get_collections().collections]:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

def fetch_utterances():
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT 
                u.id, u.dialog_id, u.content, u.speaker, u.segment_number, u.start_time, u.end_time, u.created_at,
                d.title, d.topic_id, d.tags
            FROM utterances u
            JOIN dialogs d ON d.id = u.dialog_id
            WHERE u.metadata->>'vectorized' IS DISTINCT FROM 'true'
        """)
        return cur.fetchall()

def mark_vectorized(utterance_ids):
    with pg_conn.cursor() as cur:
        cur.execute("""
            UPDATE utterances
            SET metadata = jsonb_set(COALESCE(metadata, '{}'), '{vectorized}', '"true"')
            WHERE id = ANY(ARRAY[%s]::uuid[])
        """, (utterance_ids,))
        pg_conn.commit()

def upload_embeddings():
    BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))  # по умолчанию 100

    rows = fetch_utterances()
    if not rows:
        print("No new utterances to vectorize.")
        return

    # Нарежем данные на батчи
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]

        texts = [f"query: {row[2]}" for row in batch]  # row[2] = content
        embeddings = model.encode(texts, batch_size=32, show_progress_bar=False)

        points = []
        ids = []

        for embedding, row in zip(embeddings, batch):
            (uid, dialog_id, content, speaker, seg_num, start_time, end_time, created_at,
             title, topic_id, tags) = row

            points.append(PointStruct(
                id=str(uid),
                vector=embedding.tolist(),
                payload={
                    "utterance_id": str(uid),
                    "dialog_id": str(dialog_id),
                    "speaker": speaker,
                    "segment_number": seg_num,
                    "start_time": start_time,
                    "end_time": end_time,
                    "created_at": created_at.isoformat() if created_at else None,
                    "dialog_title": title,
                    "topic_id": topic_id,
                    "tags": tags
                }
            ))
            ids.append(str(uid))

        qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        mark_vectorized(ids)

ensure_collection()
