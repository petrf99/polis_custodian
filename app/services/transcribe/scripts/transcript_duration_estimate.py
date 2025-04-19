from pydub.utils import mediainfo
from pydub import AudioSegment
import json
import os
import logging

from logging import getLogger
logger = getLogger(__name__)

SPEED_CONFIG_PATH = "services/transcript/configs/whisper_speed_factors.json"
LOAD_CONFIG_PATH = "services/transcript/configs/whisper_model_load_time.json"

if os.path.exists(SPEED_CONFIG_PATH) and os.path.exists(LOAD_CONFIG_PATH):
    with open(SPEED_CONFIG_PATH, "r") as f:
        MODEL_SPEED_FACTORS = json.load(f)
    with open(LOAD_CONFIG_PATH, "r") as f:
        MODEL_LOAD_TIME = json.load(f)
else:
    logger.info('Transcript time estimation config load failed!')
    MODEL_SPEED_FACTORS = {
        "tiny": 0.25,
        "base": 0.5,
        "small": 1.0,
        "medium": 2.0,
        "large": 4.0
    }  

    MODEL_LOAD_TIME = {
        "tiny": 1,
        "base": 2,
        "small": 4,
        "medium": 8,
        "large": 15
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