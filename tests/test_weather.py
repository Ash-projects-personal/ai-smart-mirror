from mirror_core import WeatherProvider


def test_seeded_provider_is_deterministic():
    a = WeatherProvider(seed=42).get_current()
    b = WeatherProvider(seed=42).get_current()
    assert a == b


def test_snapshot_short_format():
    snap = WeatherProvider(seed=1).get_current()
    short = snap.short()
    assert snap.location in short
    assert "°C" in short


def test_humidity_in_range():
    snap = WeatherProvider(seed=7).get_current()
    assert 40 <= snap.humidity_pct <= 90
