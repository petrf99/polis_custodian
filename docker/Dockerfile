# 📦 Базовый Python-образ
FROM python:3.10-slim

# 🛠️ Устанавливаем системные зависимости (если нужны)
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 🏗️ Устанавливаем рабочую директорию
WORKDIR /app

# 📂 Копируем все исходники
COPY ../.. /app/

ENV PIP_NO_CACHE_DIR=off

# 📦 Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r docker/requirements.txt

# ✅ Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app

# 💬 На время dev можешь переопределять команду в docker-compose
CMD ["python", "application/custodian_archetypes/chronicler/main.py"]
