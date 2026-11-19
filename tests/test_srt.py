from lang_reader.srt import Cue, parse_srt

SAMPLE = (
    "1\r\n00:00:01,000 --> 00:00:03,500\r\n<i>Bonjour</i> tout le monde\r\n\r\n"
    "2\r\n00:00:04,000 --> 00:00:05,250\r\nÇa va ?\r\n"
)


def test_parses_times_text_and_strips_markup():
    assert parse_srt(SAMPLE) == [
        Cue(1.0, 3.5, "Bonjour tout le monde"),
        Cue(4.0, 5.25, "Ça va ?"),
    ]


def test_keeps_multiline_text():
    cues = parse_srt("1\n00:00:00,000 --> 00:00:01,000\nline one\nline two\n")
    assert cues[0].text == "line one\nline two"


def test_accepts_missing_index_and_dot_milliseconds():
    cues = parse_srt("00:01:00.5 --> 00:01:02.25\nhello\n")
    assert cues == [Cue(60.5, 62.25, "hello")]


def test_hours_are_handled():
    assert parse_srt("1\n01:00:00,000 --> 01:00:01,000\nhi")[0].start == 3600.0


def test_skips_malformed_and_empty_blocks():
    content = "garbage\n\n2\n00:00:01,000 --> 00:00:02,000\n\n\n3\n00:00:03,000 --> 00:00:04,000\nok"
    assert parse_srt(content) == [Cue(3.0, 4.0, "ok")]


def test_empty_input():
    assert parse_srt("") == []
