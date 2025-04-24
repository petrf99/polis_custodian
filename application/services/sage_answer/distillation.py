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
def summarize_with_llama(promt_head, promt_tail, text: str, max_tokens: int = 150) -> str:
    prompt = f"{promt_head}\n{text.strip()}{promt_tail}"
    output = llm(prompt, max_tokens=max_tokens, stop=["</s>"])
    return output["choices"][0]["text"].strip()

# === Token counter ===
def count_tokens(text: str) -> int:
    return len(llm.tokenize(text.encode("utf-8")))

# === Делим текст на подчанки, не превышающие лимит ===
def split_text_by_token_limit(text: str, max_tokens: int) -> List[str]:
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        test_chunk = current_chunk + [word]
        test_text = " ".join(test_chunk)
        token_count = count_tokens(test_text)

        if token_count > max_tokens:
            # Добавляем предыдущий chunk (без нового слова)
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            current_chunk = [word]
        else:
            current_chunk.append(word)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# === Генерация текстов из чанков ===
def format_chunk(chunk: Dict) -> str:
    header = f"[Topic: {chunk['topic']}]\n[Dialog: {chunk['dialog']}]\n[Date: {chunk['datetime']}]\n"
    body = "\n".join(f"{u['text']}" for u in chunk['utterances'])
    return header + "\n" + clean_text(body)

# === Summarize list of texts ===
def summarize_chunks(texts: List[str]) -> List[str]:
    summaries = []

    for text in texts:
        # Выделим заголовок (всё, что в [ ] )
        lines = text.strip().split("\n")
        header_lines = [line for line in lines if line.startswith("[")]
        header = " ".join(header_lines)
        header_token_count = count_tokens(header)

        # Остальной текст — тело
        body = "\n".join(line for line in lines if not line.startswith("["))

        # Делим тело с учётом лимита
        PREFIX_TOKENS = count_tokens(PROMT_TAIL+PROMT1_HEAD)  # обычно 2
        body_chunks = split_text_by_token_limit(body, MODEL1_MAX_TOKENS - header_token_count - PREFIX_TOKENS)

        for chunk in body_chunks:
            full_chunk = f"{header}\n{chunk}"

            layer = 1
            file_path = str(Path.cwd() / f'full_chunk_{layer}.txt')
            layer += 1
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{full_chunk}\n\n\n")

            summary = summarize_with_llama(PROMT1_HEAD, PROMT_TAIL, full_chunk, max_tokens=150)
            summaries.append(summary)

    return summaries


# === Рекурсивная дистилляция ===
def recursive_distill(chunks: List[Dict]) -> List[str]:
    texts = [format_chunk(chunk) for chunk in chunks]
    summaries = summarize_chunks(texts)
    
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
