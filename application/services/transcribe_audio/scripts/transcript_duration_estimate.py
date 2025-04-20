from pydub.utils import mediainfo
from pydub import AudioSegment
import json
import os
from pathlib import Path

from logging import getLogger
logger = getLogger(__name__)

# Папка, где находится текущий файл transcript_duration_estimate.py
BASE_DIR = Path(__file__).resolve().parent

# Путь к папке configs
CONFIGS_DIR = BASE_DIR / "configs"

# Полные пути к JSON-файлам
SPEED_CONFIG_PATH = CONFIGS_DIR / "whisper_speed_factors.json"
LOAD_CONFIG_PATH = CONFIGS_DIR / "whisper_model_load_time.json"

if os.path.exists(SPEED_CONFIG_PATH) and os.path.exists(LOAD_CONFIG_PATH):
    with open(SPEED_CONFIG_PATH, "r") as f:
        MODEL_SPEED_FACTORS = json.load(f)
    with open(LOAD_CONFIG_PATH, "r") as f:
        MODEL_LOAD_TIME = json.load(f)
else:
    logger.info('Transcript time estimation config load failed!')
    MODEL_SPEED_FACTORS = {
        "tiny": 0.25,
        "base": 0.6,
        "small": 1.0,
        "medium": 1.8,
        "large": 2.7
    }  

    MODEL_LOAD_TIME = {
        "tiny": 1,
        "base": 2,
        "small": 3,
        "medium": 6,
        "large": 10
    }


def get_audio_duration(filepath):
    info = mediainfo(filepath)
    duration_sec = float(info["duration"])
    return duration_sec

def estimate_transcription_time(filepath, model_size):
    duration_sec = get_audio_duration(filepath)
    multiplier = MODEL_SPEED_FACTORS.get(model_size, 1.0)
    load_penalty = MODEL_LOAD_TIME.get(model_size, 1.0)
    estimated = duration_sec * multiplier + load_penalty
    return round(estimated)