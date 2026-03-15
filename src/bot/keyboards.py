from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup


def get_language_kb() -> InlineKeyboardMarkup:
    """inline keyboard for explanation language."""
    kb = InlineKeyboardBuilder()
    kb.button(text="English", callback_data="lang_en")
    kb.button(text="Українська", callback_data="lang_uk")
    kb.button(text="Deutsch", callback_data="lang_de")
    kb.button(text="Русский", callback_data="lang_ru")

    # adjust(2) places 2 buttons per row
    kb.adjust(2)
    return kb.as_markup()