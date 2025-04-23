import os
import math
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# === ENV config ===
MODEL1_NAME = os.getenv("MODEL1_NAME", "csebuetnlp/mT5_multilingual_XLSum")
MODEL1_MAX_TOKENS = int(os.getenv("MODEL1_MAX_TOKENS", 512))  # токенов на вход
MODEL2_MAX_TOKENS = int(os.getenv("MODEL2_MAX_TOKENS", 2048))  # финальный лимит

# === Init model-1 ===
tokenizer = AutoTokenizer.from_pretrained(MODEL1_NAME)
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
    body = "\n".join(f"{u['speaker']}: {u['text']}" for u in chunk['utterances'])
    return header + "\n" + body

# === Summarize list of texts ===
def summarize_chunks(texts: List[str]) -> List[str]:
    summaries = []
    for text in texts:
        chunks = split_text_by_token_limit(text, MODEL1_MAX_TOKENS)
        for chunk in chunks:
            summary = summarizer(chunk, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            summaries.append(summary)
    return summaries

# === Рекурсивная дистилляция ===
def recursive_distill(chunks: List[Dict]) -> List[str]:
    texts = [format_chunk(chunk) for chunk in chunks]
    summaries = summarize_chunks(texts)

    while True:
        joined = "\n\n".join(summaries)
        if count_tokens(joined) <= MODEL2_MAX_TOKENS:
            break
        summaries = summarize_chunks([joined])  # ещё один слой сжатия

    return summaries
