from mirror_core import parse_command


def test_arm_keyword():
    assert parse_command("please arm security now") == "ARM_SECURITY"


def test_alias_lock_down():
    assert parse_command("lock down the house") == "ARM_SECURITY"


def test_disarm():
    assert parse_command("DISARM the system") == "DISARM_SECURITY"


def test_unknown():
    assert parse_command("make me coffee") == "UNKNOWN"


def test_wake_word_required_present():
    assert parse_command("hey mirror, arm security", require_wake_word=True) == "ARM_SECURITY"


def test_wake_word_required_missing():
    assert parse_command("arm security", require_wake_word=True) == "NO_WAKE_WORD"


def test_quit_aliases():
    assert parse_command("quit") == "QUIT"
    assert parse_command("exit") == "QUIT"
