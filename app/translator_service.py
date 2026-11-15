from deep_translator import GoogleTranslator

def translate_word(word: str, source_lang: str, target_lang: str = "en") -> str:
    cleaned = ''.join(c for c in word if c.isalnum())
    if not cleaned:
        return word
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        translation = translator.translate(cleaned)
        return translation if translation else word
    except Exception as e:
        return f"[Translation error: {str(e)}]"