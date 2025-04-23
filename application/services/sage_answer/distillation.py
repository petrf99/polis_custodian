import os
import math
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from pathlib import Path

from application.services.text_processing.clean_text import clean_text

# === ENV config ===
MODEL1_NAME = os.getenv("MODEL1_NAME", "google/flan-t5-base")
MODEL1_MAX_TOKENS = int(os.getenv("MODEL1_MAX_TOKENS", 512))  # токенов на вход
MODEL2_MAX_TOKENS = int(os.getenv("MODEL2_MAX_TOKENS", 2048))  # финальный лимит

# === Init model-1 ===
tokenizer = AutoTokenizer.from_pretrained(MODEL1_NAME, use_fast=False)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL1_NAME)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)

# === Token counter ===
def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

# === Делим текст на подчанки, не превышающие лимит ===
def split_text_by_token_limit(text: str, max_tokens: int) -> List[str]:
    words = text.split()
    chunks = []
    current_chunk = []
    token_count = 0

    for word in words:
        token_count += count_tokens(word)
        if token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            token_count = count_tokens(word)
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
        PREFIX_TOKENS = count_tokens("summarize: ")  # обычно 2
        body_chunks = split_text_by_token_limit(body, MODEL1_MAX_TOKENS - header_token_count - PREFIX_TOKENS)

        for chunk in body_chunks:
            full_chunk = f"summarize: {header} {chunk}"

            layer = 1
            file_path = str(Path.cwd() / f'full_chunk_{layer}.txt')
            layer += 1
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"{full_chunk}\n\n\n")

            summary = summarizer(
                full_chunk,
                max_length=150,
                min_length=30,
                do_sample=False,
                truncation=True  # <- на всякий случай
            )[0]['summary_text']
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
