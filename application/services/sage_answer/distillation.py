import os
import math
from typing import List, Dict
from llama_cpp import Llama
from pathlib import Path

from application.services.text_processing.clean_text import clean_text

# === ENV config ===
MODEL_PATH = os.getenv("MODEL_PATH", "google/flan-t5-base")
MODEL1_MAX_TOKENS = int(os.getenv("MODEL1_MAX_TOKENS", 512))  # токенов на вход
MODEL2_MAX_TOKENS = int(os.getenv("MODEL2_MAX_TOKENS", 2048))  # финальный лимит

# === Init model-1 ===
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=MODEL1_MAX_TOKENS,
    n_threads=8
)

PROMT1_HEAD = os.getenv("MODEL1_PROMT_HEAD")
PROMT_TAIL = os.getenv("PROMT_TAIL")
def summarize_with_llama(promt_head, promt_tail, question, text: str, max_tokens: int = 150) -> str:
    prompt = f"{promt_head}\nQuestion:\n'{question}\n\nTexts:\n{text.strip()}\n{promt_tail}"
    output = llm(prompt, max_tokens=max_tokens, stop=["</s>"])
    return output["choices"][0]["text"].strip()

# === Token counter ===
def count_tokens(text: str) -> int:
    return len(llm.tokenize(text.encode("utf-8")))

# === Делим текст на подчанки, не превышающие лимит ===
def split_chunks_by_token_limit(texts: List[str], max_tokens: int) -> List[str]:
    chunks = []
    current_chunk = ''

    separator = '\n------------------------\n'

    layer = 1
    for text in texts:
        test_chunk = current_chunk + text + separator
        token_count = count_tokens(test_chunk)

        if token_count > max_tokens:
            # Добавляем предыдущий chunk (без нового слова)
            if current_chunk:
                chunks.append(current_chunk)

                file_path = str(Path.cwd() / f'chunks_split_{layer}.txt')
                layer += 1
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(current_chunk)

            current_chunk = text + separator
        else:
            current_chunk = test_chunk

    if current_chunk not in ('', separator):
        chunks.append(current_chunk)

    return chunks


# === Генерация текстов из чанков ===
def format_chunk(chunk: Dict) -> str:
    header = f"[Topic: {chunk['topic']}]\n[Dialog: {chunk['dialog']}]\n[Date: {chunk['datetime']}]\n"
    body = "\n".join(f"{u['text']}" for u in chunk['utterances'])
    return header + "\n" + clean_text(body)

# === Summarize list of texts ===
def summarize_chunks(question, texts: List[str]) -> List[str]:
    summaries = []

    for text in texts:
        summary = summarize_with_llama(PROMT1_HEAD, PROMT_TAIL, question, text, max_tokens=512)
        summaries.append(summary)

    return summaries


# === Рекурсивная дистилляция ===
def recursive_distill(question, chunks: List[Dict]) -> List[str]:
    PREFIX_TOKENS = count_tokens(PROMT_TAIL+PROMT1_HEAD)
    TOKEN_DELTA = 100
    texts = split_chunks_by_token_limit([format_chunk(chunk) for chunk in chunks], MODEL1_MAX_TOKENS - (PREFIX_TOKENS+TOKEN_DELTA))

    summaries = summarize_chunks(question, texts)
    
    layer = 1
    file_path = str(Path.cwd() / f'summaries_{layer}.txt')
    layer += 1
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"[NUMBER OF SUMMARIES] {len(summaries)}\n\n")
        for i, summary in enumerate(summaries, start=1):
            f.write(f"[SUMMARY {i}]\n{summary.strip()}\n\n")

    while True:
        joined = "\n\n".join(summaries)
        if count_tokens(joined) <= MODEL2_MAX_TOKENS:
            break
        summaries = summarize_chunks([joined])  # ещё один слой сжатия

        file_path = str(Path.cwd() / f'summaries_{layer}.txt')
        layer += 1
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"[NUMBER OF SUMMARIES] {len(summaries)}\n\n")
            for i, summary in enumerate(summaries, start=1):
                f.write(f"[SUMMARY {i}]\n{summary.strip()}\n\n")

    return summaries
