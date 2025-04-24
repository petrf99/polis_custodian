from logging import getLogger
logger = getLogger(__name__)

from application.tech_utils.safe_func_run import safe_run_sync
from application.services.sage_answer.vectorize import * 
from application.services.sage_answer.context_builder import *
from application.services.sage_answer.distillation import recursive_distill
from application.services.sage_answer.final_answer_generator import final_context, answer

from pathlib import Path
import os


@safe_run_sync
def sage_answer_worker(data: dict):
    question_vector = embed_question(data['question'])
    sim_vectors = search_similar_vectors(question_vector, 1, 'sage_cache')
    chunks = build_chunks_from_vector(question_vector, data['search_width'], data['search_depth'])
    summaries = recursive_distill(chunks)
    #upsert_to_sage_cache(question_vector, data, 'test_context', sim_vectors[0]['score'], True)
    context = final_context("\n\n".join(summaries), data['question'])
    return answer(context, data['question'])