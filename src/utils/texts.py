# src/utils/texts.py

SUPPORTED_LANGUAGES = ["en", "uk", "de", "ru"]
DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        "welcome_new": "Welcome to satzfix!\n\nPlease choose the language for explanations and translations:",
        "welcome_back": "Welcome back, {name}!\n\nI am ready. Just send me your German sentences.",
        "choose_new_language": "Please choose the new language for explanations:",
        "lang_saved": "Language has been successfully saved! Send me a sentence in German.",
        "quota_exceeded": "Daily limit reached. Try again tomorrow.",
        "text_too_long": "Your text is too long.",
        "not_german": "Please enter a sentence in German.",
        "original": "Original:",
        "corrected": "Corrected:",
        "translated": "Translated:",
        "errors_title": "Errors:",
        "no_errors": "Perfect! No errors found.",
        "analysis_error": "An error occurred during the analysis.",
        "role_changed": "Your role has been changed to \"{role}\".",
        "role_desc_regular": "Your daily limit is now 5 sentences, and the message length limit is 250 characters.",
        "role_desc_admin": "Your daily limit is now 15 sentences, and the message length limit is 500 characters. For longer texts, a more powerful model will now be used.",
        "role_desc_owner": "You can now use the bot without any restrictions. For longer texts, a more powerful model will now be used.",
        "cmd_change_lang_desc": "Change the language for explanations",
        "loading_errors": "Loading errors",
        "analyzing": "Analyzing text",
        "require_language_selection": "Please choose the language for translation and explanations",
        "error_text_too_long": "Text is too long ({current_len}/{char_limit} characters). Please split it into smaller parts or ask the bot creator to increase your limit: @Kozaknazar",
        "error_daily_limit_reached": "Daily request limit reached ({req_limit}/{req_limit}). Please try again tomorrow or ask the bot creator to get more daily requests: @Kozaknazar",
        "bot_short_description": "I correct German sentences and explain your mistakes using CEFR rules.",
        "bot_welcome_description": (
            "Welcome to the German Error Analyzer! 🇩🇪\n\n"
            "Learning German? Don't guess if your sentence is correct. "
            "Just send me your text and I will:\n\n"
            "✨ Fix grammar and spelling mistakes\n"
            "📝 Explain the rules clearly\n"
            "🌐 Translate it to your language\n\n"
            "Press /start to begin!"
        ),
    },
    "uk": {
        "welcome_new": "Ласкаво просимо до satzfix!\n\nБудь ласка, оберіть мову для пояснень та перекладів:",
        "welcome_back": "З поверненням, {name}!\n\nЯ готовий. Просто надішліть мені ваші речення німецькою.",
        "choose_new_language": "Будь ласка, оберіть нову мову для пояснень:",
        "lang_saved": "Мову успішно збережено! Надішліть мені речення німецькою.",
        "quota_exceeded": "Денний ліміт вичерпано. Спробуйте завтра.",
        "text_too_long": "Текст занадто довгий.",
        "not_german": "Будь ласка, введіть речення німецькою.",
        "original": "Оригінал:",
        "corrected": "Виправлено:",
        "translated": "Переклад:",
        "errors_title": "Помилки:",
        "no_errors": "Ідеально! Помилок не знайдено.",
        "analysis_error": "Сталася помилка під час аналізу.",
        "role_changed": "Ваша роль була змінена на \"{role}\".",
        "role_desc_regular": "Тепер ваш денний ліміт 5 речень і обмеження 250 символів на повідомлення.",
        "role_desc_admin": "Тепер ваш денний ліміт 15 речень і обмеження 500 символів на повідомлення. Для довших текстів тепер буде використовуватись більш потужна модель.",
        "role_desc_owner": "Тепер ви можете без обмежень користуватись ботом. Для довших текстів тепер буде використовуватись більш потужна модель.",
        "cmd_change_lang_desc": "Змінити мову пояснень",
        "loading_errors": "Завантаження помилок",
        "analyzing": "Аналізую текст",
        "require_language_selection": "Будь ласка, виберіть мову перекладу та пояснень",
        "error_text_too_long": "Текст занадто довгий ({current_len}/{char_limit} символів). Будь ласка, розділіть його на менші частини або попросіть розробника збільшити ваш ліміт: @Kozaknazar",
        "error_daily_limit_reached": "Денний ліміт запитів вичерпано ({req_limit}/{req_limit}). Спробуйте завтра або попросіть розробника надати більше запитів: @Kozaknazar",
        "bot_short_description": "🇩🇪 Я виправляю німецькі речення та пояснюю помилки за стандартами CEFR.",
        "bot_welcome_description": (
            "Привіт! Я твій особистий помічник з німецької мови 🇩🇪\n\n"
            "Вчиш німецьку і сумніваєшся, чи правильно побудоване речення? "
            "Просто відправ мені свій текст, і я:\n\n"
            "✨ Виправлю граматику та орфографію\n"
            "📝 Поясню правила зрозумілою мовою\n"
            "🌐 Додам переклад\n\n"
            "Натискай /start, щоб почати!"
        ),
    },
    "de": {
        "welcome_new": "Willkommen bei satzfix!\n\nBitte wählen Sie die Sprache für Erklärungen und Übersetzungen:",
        "welcome_back": "Willkommen zurück, {name}!\n\nIch bin bereit. Senden Sie mir einfach Ihre deutschen Sätze.",
        "choose_new_language": "Bitte wählen Sie die neue Sprache für Erklärungen:",
        "lang_saved": "Sprache wurde gespeichert! Senden Sie mir einen Satz auf Deutsch.",
        "quota_exceeded": "Tageslimit erreicht. Versuchen Sie es morgen nochmal.",
        "text_too_long": "Ihr Text ist zu lang.",
        "not_german": "Bitte geben Sie einen Satz auf Deutsch ein.",
        "original": "Original:",
        "corrected": "Korrigiert:",
        "translated": "Übersetzt:",
        "errors_title": "Fehler:",
        "no_errors": "Perfekt! Keine Fehler gefunden.",
        "analysis_error": "Ein Fehler ist während der Analyse aufgetreten.",
        "role_changed": "Ihre Rolle wurde auf \"{role}\" geändert.",
        "role_desc_regular": "Ihr Tageslimit beträgt nun 5 Sätze und die maximale Nachrichtenlänge 250 Zeichen.",
        "role_desc_admin": "Ihr Tageslimit beträgt nun 15 Sätze und die maximale Nachrichtenlänge 500 Zeichen. Für längere Texte wird nun ein leistungsfähigeres Modell verwendet.",
        "role_desc_owner": "Sie können den Bot nun uneingeschränkt nutzen. Für längere Texte wird nun ein leistungsfähigeres Modell verwendet.",
        "cmd_change_lang_desc": "Sprache für Erklärungen ändern",
        "loading_errors": "Lade Fehler",
        "analyzing": "Text wird analysiert",
        "require_language_selection": "Bitte wählen Sie die Sprache für Übersetzung und Erklärungen",
        "error_text_too_long": "Text ist zu lang ({current_len}/{char_limit} Zeichen). Bitte teilen Sie ihn in kleinere Teile auf oder bitten Sie den Bot-Ersteller, Ihr Limit zu erhöhen: @Kozaknazar",
        "error_daily_limit_reached": "Tägliches Anfrage-Limit erreicht ({req_limit}/{req_limit}). Bitte versuchen Sie es morgen wieder oder bitten Sie den Bot-Ersteller um mehr tägliche Anfragen: @Kozaknazar",
        "bot_short_description": "🇩🇪 Ich korrigiere deutsche Sätze und erkläre Fehler nach CEFR-Regeln.",
        "bot_welcome_description": (
            "Willkommen beim German Error Analyzer! 🇩🇪\n\n"
            "Lernen Sie Deutsch? Raten Sie nicht, ob Ihr Satz richtig ist. "
            "Senden Sie mir einfach Ihren Text und ich werde:\n\n"
            "✨ Grammatik- und Rechtschreibfehler korrigieren\n"
            "📝 Die Regeln klar erklären\n"
            "🌐 Den Text in Ihre Sprache übersetzen\n\n"
            "Klicken Sie auf /start, um zu beginnen!"
        ),
    },
    "ru": {
        "welcome_new": "Добро пожаловать в satzfix!\n\nПожалуйста, выберите язык для объяснений и переводов:",
        "welcome_back": "С возвращением, {name}!\n\nЯ готов. Просто отправьте мне ваши предложения на немецком.",
        "choose_new_language": "Пожалуйста, выберите новый язык для объяснений:",
        "lang_saved": "Язык успешно сохранен! Отправьте мне предложение на немецком.",
        "quota_exceeded": "Дневной лимит исчерпан. Попробуйте завтра.",
        "text_too_long": "Текст слишком длинный.",
        "not_german": "Пожалуйста, введите предложение на немецком.",
        "original": "Оригинал:",
        "corrected": "Исправлено:",
        "translated": "Перевод:",
        "errors_title": "Ошибки:",
        "no_errors": "Идеально! Ошибок не найдено.",
        "analysis_error": "Произошла ошибка во время анализа.",
        "role_changed": "Ваша роль была изменена на \"{role}\".",
        "role_desc_regular": "Теперь ваш дневной лимит 5 предложений и ограничение 250 символов на сообщение.",
        "role_desc_admin": "Теперь ваш дневной лимит 15 предложений и ограничение 500 символов на сообщение. Для длинных текстов теперь будет использоваться более мощная модель.",
        "role_desc_owner": "Теперь вы можете без ограничений пользоваться ботом. Для длинных текстов теперь будет использоваться более мощная модель.",
        "cmd_change_lang_desc": "Изменить язык объяснений",
        "loading_errors": "Загрузка ошибок",
        "analyzing": "Анализ текста",
        "require_language_selection": "Пожалуйста, выберите язык перевода и объяснений",
        "error_text_too_long": "Текст слишком длинный ({current_len}/{char_limit} символов). Пожалуйста, разделите его на части или попросите создателя бота увеличить ваш лимит: @Kozaknazar",
        "error_daily_limit_reached": "Дневной лимит запросов исчерпан ({req_limit}/{req_limit}). Пожалуйста, попробуйте завтра или попросите создателя бота дать больше запросов: @Kozaknazar",
        "bot_short_description": "🇩🇪 Я исправляю немецкие предложения и объясняю ошибки по правилам CEFR.",
        "bot_welcome_description": (
            "Привет! Я твой личный помощник по немецкому языку 🇩🇪\n\n"
            "Учишь немецкий и сомневаешься, правильно ли построено предложение? "
            "Просто отправь мне свой текст, и я:\n\n"
            "✨ Исправлю грамматику и орфографию\n"
            "📝 Объясню правила понятным языком\n"
            "🌐 Добавлю перевод\n\n"
            "Нажимай /start, чтобы начать!"
        ),
    }
}

def get_text(lang_code: str, key: str) -> str:
    # Fallback to default language if the requested language or key is missing
    lang = lang_code if lang_code in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    return TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE]).get(key, f"missing_text: {key}")