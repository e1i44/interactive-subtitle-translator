from lang_reader.files import find_audio, infer_language, list_srt_files


def test_infer_language_from_double_extension():
    assert infer_language("episode.fr.srt") == "fr"
    assert infer_language("some/dir/show.pt-BR.srt") == "pt-BR"


def test_infer_language_returns_blank_when_absent():
    assert infer_language("episode.srt") == ""
    assert infer_language("my.long.title.srt") == ""


def test_find_audio_prefers_language_named_mp3(tmp_path):
    srt = tmp_path / "show.fr.srt"
    (tmp_path / "show.mp3").touch()
    (tmp_path / "show.fr.mp3").touch()
    assert find_audio(srt) == tmp_path / "show.fr.mp3"


def test_find_audio_falls_back_to_name_without_language(tmp_path):
    (tmp_path / "show.mp3").touch()
    assert find_audio(tmp_path / "show.fr.srt") == tmp_path / "show.mp3"


def test_find_audio_none_when_missing(tmp_path):
    assert find_audio(tmp_path / "show.fr.srt") is None

def test_list_srt_files_filters_and_sorts(tmp_path):
    for name in ["b.fr.srt", "a.fr.srt", "a.fr.mp3", "notes.txt"]:
        (tmp_path / name).touch()
    assert [p.name for p in list_srt_files(tmp_path)] == ["a.fr.srt", "b.fr.srt"]


def test_list_srt_files_missing_folder(tmp_path):
    assert list_srt_files(tmp_path / "nope") == []