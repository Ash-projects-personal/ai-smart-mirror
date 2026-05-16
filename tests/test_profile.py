from mirror_core import FaceRecognizer


def test_direct_user_id_match():
    rec = FaceRecognizer()
    assert rec.identify("ashish").user_id == "ashish"
    assert rec.identify("guest").user_id == "guest"


def test_none_returns_default():
    assert FaceRecognizer().identify(None).user_id == "ashish"


def test_unknown_frame_is_deterministic():
    rec = FaceRecognizer()
    assert rec.identify("xyz-frame-123").user_id == rec.identify("xyz-frame-123").user_id
