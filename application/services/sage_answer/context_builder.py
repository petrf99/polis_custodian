import os
from typing import List, Dict, Tuple, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import SearchRequest

# === Конфиг ===
SEARCH_DEPTH = int(os.getenv("SAGE_SEARCH_DEPTH", 5))
SEARCH_WIDTH = int(os.getenv("SAGE_SEARCH_WIDTH", 3))
POSTGRES_URL = os.getenv("POSTGRES_URL")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
UTTERANCE_COLLECTION = os.getenv("SAGE_UTTERANCE_COLLECTION", "utterances")

qdrant = QdrantClient(QDRANT_URL)

# === Подключение к Postgres ===
def get_pg_conn():
    from urllib.parse import urlparse
    result = urlparse(POSTGRES_URL)
    return psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# === Основная функция: вектор → чанк-и ===
import os
from typing import List, Dict, Any
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient

SEARCH_DEPTH = int(os.getenv("SAGE_SEARCH_DEPTH", 3))
POSTGRES_URL = os.getenv("POSTGRES_URL")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
UTTERANCE_COLLECTION = os.getenv("SAGE_UTTERANCE_COLLECTION", "utterances")

qdrant = QdrantClient(QDRANT_URL)

# === Соединение с PostgreSQL ===
def get_pg_conn():
    from urllib.parse import urlparse
    result = urlparse(POSTGRES_URL)
    return psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# === Слияние перекрывающихся окон ===
def merge_windows(windows: List[Tuple[int, int]], window_size: int = 10) -> List[Tuple[int, int]]:
    if not windows:
        return []

    # === Слияние перекрывающихся окон ===
    sorted_windows = sorted(windows)
    merged = [sorted_windows[0]]

    for start, end in sorted_windows[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # пересекаются
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    # === Делим каждый слитый интервал на окна по N ===
    split_windows = []
    for start, end in merged:
        current = start
        while current <= end:
            window_end = min(current + window_size - 1, end)
            split_windows.append((current, window_end))
            current += window_size

    return split_windows


# === Основная функция ===
def build_chunks_from_vector(vector: List[float], search_width: int, depth: int = SEARCH_DEPTH) -> List[Dict[str, Any]]:
    chunks = []
    conn = get_pg_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 1. Qdrant: поиск релевантных реплик
    hits = qdrant.search(
        collection_name=UTTERANCE_COLLECTION,
        query_vector=vector,
        limit=search_width,
        with_payload=True
    )

    # 2. Группировка окон по dialog_id
    dialog_windows = defaultdict(list)
    utterance_ids_by_dialog = defaultdict(list)

    for hit in hits:
        payload = hit.payload
        dialog_id = payload["dialog_id"]
        center = payload["segment_number"]
        window = (center - depth, center + depth)
        dialog_windows[dialog_id].append(window)
        utterance_ids_by_dialog[dialog_id].append(payload["utterance_id"])

    # 3. По каждому диалогу — собрать объединённый чанк
    for dialog_id, raw_windows in dialog_windows.items():
        ranges = merge_windows(raw_windows)

        cursor.execute("""
                SELECT d.title AS dialog_title, d.started_at::date, t.name AS topic_name
                FROM dialogs d
                JOIN topics t ON d.topic_id = t.id
                WHERE d.id = %s;
        """, (dialog_id,))
        meta = cursor.fetchone()

        for (start, end) in ranges:
            clause = f"segment_number BETWEEN {start} AND {end}"
            cursor.execute(f"""
                SELECT speaker, content, segment_number
                FROM utterances
                WHERE dialog_id = %s AND ({clause})
                ORDER BY segment_number;
            """, (dialog_id,))
            utterances = cursor.fetchall()

            chunk = {
                "topic": meta["topic_name"],
                "dialog": meta["dialog_title"],
                "datetime": meta["started_at"].isoformat() if meta["started_at"] else None,
                "dialog_id": dialog_id,
                "source_utterance_ids": utterance_ids_by_dialog[dialog_id],
                "utterances": [
                    {"text": row["content"]}
                    for row in utterances
                ]
            }

            chunks.append(chunk)

    cursor.close()
    conn.close()
    return chunks



def format_chunks_for_telegram(chunks: List[Dict[str, Any]], max_chunks: int = 3) -> str:
    parts = []
    for i, chunk in enumerate(chunks[:max_chunks]):
        header = f"<b>🧠 Chunk {i+1}</b>\n" \
                 f"<i>Topic:</i> {chunk['topic']}\n" \
                 f"<i>Dialog:</i> {chunk['dialog']}\n" \
                 f"<i>Date:</i> {chunk['datetime']}\n\n"

        utterances = "\n".join(
            f"{u['text']}" for u in chunk["utterances"]
        )

        parts.append(header + utterances)

    return "\n\n".join(parts)


def format_chunks_as_prompt(chunks: List[Dict[str, Any]], max_chunks: int = 3) -> str:
    prompt_parts = []
    for i, chunk in enumerate(chunks[:max_chunks]):
        header = f"[Chunk {i+1}]\n" \
                 f"Topic: {chunk['topic']}\n" \
                 f"Dialog: {chunk['dialog']}\n" \
                 f"Date: {chunk['datetime']}\n\n"

        utterances = "\n".join(
            f"{u['text']}" for u in chunk["utterances"]
        )

        prompt_parts.append(header + utterances)

    return "\n\n".join(prompt_parts)

