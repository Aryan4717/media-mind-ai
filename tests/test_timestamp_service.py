from app.services.timestamp_service import TimestampService


def test_text_overlap_basic():
    assert TimestampService._text_overlap("machine learning", "machine learning is fun", threshold=0.3)
    assert not TimestampService._text_overlap("totally different", "machine learning", threshold=0.3)


def test_merge_overlapping_segments():
    segments = [
        {"start": 0.0, "end": 5.0, "text": "a", "duration": 5.0},
        {"start": 6.0, "end": 8.0, "text": "b", "duration": 2.0},  # within gap_threshold=2.0 (6 <= 5+2)
        {"start": 20.0, "end": 22.0, "text": "c", "duration": 2.0},
    ]
    merged = TimestampService._merge_overlapping_segments(segments, gap_threshold=2.0)
    assert len(merged) == 2
    assert merged[0]["start"] == 0.0
    assert merged[0]["end"] == 8.0
    assert "a" in merged[0]["text"] and "b" in merged[0]["text"]


def test_format_timestamp():
    assert TimestampService.format_timestamp(10.5) == "00:10.500"
    assert TimestampService.format_timestamp(61.2) == "01:01.200"


