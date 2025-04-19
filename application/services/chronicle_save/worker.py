import json
import uuid
import psycopg2
import os
from datetime import datetime, timedelta
from pathlib import Path

from logging import getLogger
logger = getLogger(__name__)

POSTGRES_URL = os.getenv("POSTGRES_URL")

def load_json(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def insert_utterances(utterances: list[dict]):
    logger.info("[INSERT DATA TO PGSQL. CONNECT TO DB]")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    logger.info("[INSERT DATA TO PGSQL. CONNECTION ESTABLISHED]")

    dialog_insert_query = """
        INSERT INTO dialogs (
            id,
            title,
            started_at ,
            ended_at,
            topic_id,
            tags,
            source,
            participants,
            summary,
            metadata
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

    logger.info("[INSERT DIALOG]")
    cursor.execute(
            dialog_insert_query,
            (
                utterances[0]["dialog_id"], #dialog_id
                "TEST_" + str(datetime.now()), #title
                datetime.fromisoformat(utterances[0]["created_at"]) + timedelta(seconds=utterances[0]["start_time"]), #started_at
                datetime.fromisoformat(utterances[0]["created_at"]) + timedelta(seconds=utterances[-1]["end_time"]), #ended_at
                0, #topic_id
                [], #tags
                "", #source
                [], #participants
                "", #summary
                json.dumps({}), #metadata
            )
        )

    utt_insert_query = """
    INSERT INTO utterances (
        id, dialog_id, speaker, content,
        start_time, end_time, segment_number,
        created_at, metadata
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    logger.info("[INSERT UTTERANCES]")
    for u in utterances:
        cursor.execute(
            utt_insert_query,
            (
                u["id"],
                u["dialog_id"],
                u.get("speaker"),
                u["content"],
                u["start_time"],
                u["end_time"],
                u["segment_number"],
                u.get("created_at", datetime.now()),
                json.dumps(u.get("metadata", {})),
            )
        )

    conn.commit()
    cursor.close()
    conn.close()
    logger.info(f"Uploaded {len(utterances)} utterances to Postgres successfully")

from safe_func_dec import safe_run_sync
@safe_run_sync
def run_import(json_path: str):
    logger.info(f"[IMPORT] Загрузка из {json_path}")
    data = load_json(json_path)
    insert_utterances(data)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        logger.info("Use: python import_utterances.py path/to/utterances.json")
    else:
        run_import(sys.argv[1])