import psycopg2
from urllib.parse import urlparse
import os
from pathlib import Path

from logging import getLogger
logger = getLogger(__name__)

def init_db():
    logger.info("[CHR. START CREATING TABLES]")
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
    sql_path = os.path.join(base_path, 'sql_scripts', 'create_tables.sql')
    logger.info(f"SQL_PATH: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    logger.info("CHR. Execute CREATE TABLEs")
    cursor.execute(schema_sql)
    conn.commit()
    cursor.close()
    conn.close()

    logger.info("[CHR. TABLES SUCCESSFULLY CREATED]")