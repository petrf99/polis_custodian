from application.services.sage_answer.distillation import llm, summarize_with_llama, count_tokens
import os
from pathlib import Path

PROMT2_HEAD = os.getenv("MODEL2_PROMT_HEAD")
PROMT_TAIL = os.getenv("PROMT_TAIL")
MODEL3_MAX_TOKENS = int(os.getenv("MODEL3_MAX_TOKENS", 2048))

def final_context(text, question): 
    context = summarize_with_llama(PROMT2_HEAD, PROMT_TAIL, text, MODEL3_MAX_TOKENS - count_tokens(question + PROMT2_HEAD + PROMT_TAIL))
    with open(Path.cwd() / 'final_context.txt', 'w') as f:
        f.write(context)
    return context


PROMT3_HEAD = os.getenv("MODEL3_PROMT_HEAD")
def answer(context, question):
    prompt = f"{PROMT3_HEAD}\n\n"
    output = llm(prompt+'Контекст:\n'+context+'\n\nВопрос:\n'+question+PROMT_TAIL, max_tokens=4096, stop=["</s>"])
    return output["choices"][0]["text"].strip()

