from logging import getLogger
logger = getLogger(__name__)

from application.tech_utils.safe_func_run import safe_run_sync
from application.services.sage_answer.vectorize import * 
from application.services.sage_answer.context_builder import *
from application.services.sage_answer.distillation import recursive_distill
from application.services.sage_answer.final_answer_generator import final_context, answer

import os


@safe_run_sync
def sage_answer_worker(data: dict):
    question_vector = embed_question(data['question'])
    if data['use_cache']:
        sim_vectors = search_similar_vectors(question_vector, 1, 'sage_cache')
        if sim_vectors:
            score = sim_vectors[0]['score']
        else:
            score = 0.0
    else:
        score = 0.0
    if score >= float(os.getenv("CACHE_SCORE_THRESHOLD", 0.9)):
        closest_vector = sim_vectors[0]['payload']['question_id']
        conn = get_pg_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"select * from sage_questions_cache where question_id = \'{closest_vector}\'")
        context = cursor.fetchone()['context']
        cached = 'CACHED'
    else:    
        cached = 'UNCACHED'
        chunks = build_chunks_from_vector(question_vector, data['search_width'], data['search_depth'])
        summaries = recursive_distill(data['question'], chunks)
        context = "\n\n".join(summaries) # final_context("\n\n".join(summaries), data['question'])
    answ = answer(context, data['question'])
    # upsert_to_sage_cache(question_vector, data, context, sim_vectors[0]['score'], True)
    return cached + '\n\n' + context + '\n\n' + answ