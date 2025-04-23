import psycopg2
from urllib.parse import urlparse
import os

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct

from logging import getLogger
logger = getLogger(__name__)

def init_db():
    logger.info("[SG. START CREATING PSQL TABLES]")
    POSTGRES_URL = os.getenv("POSTGRES_URL")
    result = urlparse(POSTGRES_URL)
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    cursor = conn.cursor()

    base_path = os.path.dirname(__file__)
    sql_path = os.path.join(base_path, 'sql_scripts', 'create_cache_table.sql')
    logger.info(f"SQL_PATH: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    logger.info("SG. Execute CREATE TABLEs")
    cursor.execute(schema_sql)
    conn.commit()
    cursor.close()
    conn.close()

    logger.info("[SG. PSQL TABLES SUCCESSFULLY CREATED]")

    logger.info("[SG. ENSURING QDRANT CACHE]")

    # --- Конфиг ---
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

    COLLECTION_NAME = "sage_cache"
    VECTOR_SIZE = 768  # зависит от модели

    # --- Модель и клиенты ---
    qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    if COLLECTION_NAME not in [col.name for col in qdrant.get_collections().collections]:
        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )
    
    logger.info("[SG. QDRANT CACHE ENSURED]")