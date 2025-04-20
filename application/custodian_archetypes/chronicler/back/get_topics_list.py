import psycopg2
from urllib.parse import urlparse
import os

from logging import getLogger
logger = getLogger(__name__)

def get_topics_list():
    logger.info("[GETTING LIST OF TOPICS]")
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

    cursor.execute('''
    SELECT ID, NAME
    FROM TOPICS;
    ''')
    topics = cursor.fetchall()
    cursor.close()
    conn.close()

    logger.info("[RETURN LIST OF TOPICS]")
    return topics