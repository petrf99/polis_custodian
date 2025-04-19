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

    # Temperature buttons
    temp_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="0.0 (accurate)", callback_data="temp_0.0"),
        InlineKeyboardButton(text="0.5 (balanced)", callback_data="temp_0.5")],
        [InlineKeyboardButton(text="1.0 (creative)", callback_data="temp_1.0")],
        [InlineKeyboardButton(text="Use default", callback_data="temp_default")]
    ])

    # Output type buttons
    output_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔤 Full Text", callback_data="output_text"),
        InlineKeyboardButton(text="🔄 Info only", callback_data="output_info")]
    ])

    return start_kb, language_kb, model_kb, temp_kb, output_kb