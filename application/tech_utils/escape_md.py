import re

def escape_md(text: str) -> str:
    escape_chars = r"*_[]()~`>#+-=|{}.!\\"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)