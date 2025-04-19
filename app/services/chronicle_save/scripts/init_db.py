import psycopg2
from urllib.parse import urlparse
import os

from logging import getLogger
logger = getLogger(__name__)

def init_db():
    logger.info("[START CREATING TABLES]")
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

    with open("jobs/db/sql_scripts/create_tables.sql", "r", encoding="utf-8") as f:
        schema_sql = f.read()

    logger.info("Execute CREATE TABLEs")
    cursor.execute(schema_sql)
    conn.commit()
    cursor.close()
    conn.close()

    logger.info("[TABLES SUCCESSFULLY CREATED]")