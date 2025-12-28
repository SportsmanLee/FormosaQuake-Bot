import pytest

from parsing.csv_parser import decode_big5, parse_csv
from parsing.normalize import normalize_row
from policies.keys import build_event_key


SAMPLE_CSV = """編號,地震時間,經度,緯度,規模,深度,最大震度,位置
156   ,2025-12-27 23:05:55,122.079,24.69,7,72.8,4,宜蘭縣政府東方  32.3  公里 (位於臺灣東部海域)(臺灣東部海域)
小區域有感地震,2025-12-27 21:07:36,121.08,22.9057,3.6,11.2,2,臺東縣政府北北西方  18.2  公里 (位於臺東縣鹿野鄉)(臺東縣鹿野鄉)
"""


def test_decode_and_parse_csv():
    data = SAMPLE_CSV.encode("big5", errors="ignore")
    text = decode_big5(data)
    rows = parse_csv(text)
    assert len(rows) == 2
    assert rows[0]["編號"].strip() == "156"
    assert rows[1]["編號"].strip() == "小區域有感地震"


def test_normalize_row_numeric_id():
    data = SAMPLE_CSV.encode("big5", errors="ignore")
    rows = parse_csv(decode_big5(data))
    ev = normalize_row(rows[0])
    assert ev.event_key.startswith("E:")
    assert ev.intensity_value == 4.0
    assert ev.magnitude == pytest.approx(7.0)
    assert ev.depth_km == pytest.approx(72.8)


def test_normalize_row_fallback_hash():
    data = SAMPLE_CSV.encode("big5", errors="ignore")
    rows = parse_csv(decode_big5(data))
    ev = normalize_row(rows[1])
    assert ev.event_key.startswith("H:")
    assert ev.intensity_value == 2.0
    assert ev.magnitude == pytest.approx(3.6)