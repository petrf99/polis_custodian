from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_buttons():
    # Start button
    start_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Send file", callback_data="start_session")]
    ])

    # Language selection buttons
    language_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="English", callback_data="lang_en"),
        InlineKeyboardButton(text="Russian", callback_data="lang_ru")],
        [InlineKeyboardButton(text="Español", callback_data="lang_es"),
        InlineKeyboardButton(text="Auto", callback_data="lang_auto")]
    ])

    # Whisper model size buttons
    model_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="tiny(x0.25)", callback_data="model_tiny"),
        InlineKeyboardButton(text="base(x0.5)", callback_data="model_base")],
        [InlineKeyboardButton(text="small(x1.0)", callback_data="model_small"),
        InlineKeyboardButton(text="medium(x2.0)", callback_data="model_medium"),
        InlineKeyboardButton(text="large(x4.0)", callback_data="model_large")]
    ])

    # Output type buttons
    output_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Full Text", callback_data="output_text"),
        InlineKeyboardButton(text="🔄 Info only", callback_data="output_info")]
    ])

    return start_kb, language_kb, model_kb, output_kb