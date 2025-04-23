import re
import json

def extract_text_and_config(msg: str):
    """
    Returns: (text_without_config, config_dict)
    """
    # Находит JSON-подобный блок в конце строки
    match = re.search(r'({.*})\s*$', msg.strip())
    if match:
        json_part = match.group(1)
        try:
            config = json.loads(json_part)
            text = msg[:match.start()].strip()
            return text, config
        except json.JSONDecodeError:
            pass  # Если невалидный JSON — просто возвращаем всё как текст
    return msg.strip(), {}
