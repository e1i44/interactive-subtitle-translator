from lang_reader.words import find_words


def words(text):
    return [text[a:b] for a, b in find_words(text)]


def test_keeps_apostrophes_and_hyphens_inside_words():
    assert words("L'homme, peut-être ça va ?") == ["L'homme", "peut-être", "ça", "va"]


def test_ignores_numbers_and_punctuation():
    assert words("42 -- ... !") == []


def test_non_latin_scripts():
    assert words("Привет, мир") == ["Привет", "мир"]


def test_offsets_index_original_text():
    assert find_words("ab cd") == [(0, 2), (3, 5)]
