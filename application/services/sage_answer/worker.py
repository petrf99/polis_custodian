from logging import getLogger
logger = getLogger(__name__)

from application.tech_utils.safe_func_run import safe_run_sync
from application.services.sage_answer.vectorize import * #upsert_to_sage_cache, embed_question, search_similar_vectors
from application.services.sage_answer.context_builder import *

from pathlib import Path
import os


@safe_run_sync
def sage_answer_worker(data: dict):
    question_vector = embed_question(data['question'])
    sim_vectors = search_similar_vectors(question_vector, 1, 'sage_cache')
    chunks = build_chunks_from_vector(question_vector, data['search_width'], data['search_depth'])
    upsert_to_sage_cache(question_vector, data, 'test_context', sim_vectors[0]['score'], True)
    file_path = str(Path.cwd() / 'chunks.txt')
    with open(file_path, 'w') as f:
        f.write(f"[NUMBER OF CHUNKS] {len(chunks)}\n{format_chunks_as_prompt(chunks, 5)}")
    return file_path