# task_config.py
import json
import os
import builtins  # нужно для преобразования строк в классы (например "Exception" -> Exception)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_PATH = os.path.join(BASE_DIR, "configs/task_policies.json")

with open(POLICY_PATH, "r") as f:
    raw_policies = json.load(f)

def parse_policy(task_name: str):
    config = raw_policies.get(task_name, {})
    
    # Преобразуем "Exception" -> Exception (через builtins)
    if "autoretry_for" in config:
        config["autoretry_for"] = tuple(getattr(builtins, name) for name in config["autoretry_for"])

    return config
