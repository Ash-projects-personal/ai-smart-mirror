import json

from mirror_core import (
    EventLog,
    IntruderDetectionSystem,
    SnapshotCapture,
)


def test_arm_disarm_records_events(tmp_path):
    events = EventLog(tmp_path / "events.jsonl")
    sec = IntruderDetectionSystem(events=events)

    sec.arm()
    assert sec.armed is True
    sec.disarm()
    assert sec.armed is False

    lines = (tmp_path / "events.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["event"] == "armed"
    assert json.loads(lines[1])["event"] == "disarmed"


def test_alert_captures_snapshot_and_logs(tmp_path):
    events = EventLog(tmp_path / "events.jsonl")
    snap = SnapshotCapture(tmp_path / "snapshots")
    sec = IntruderDetectionSystem(events=events, snapshot=snap)

    sec.send_sms_alert()

    assert sec.last_snapshot is not None
    assert sec.last_snapshot.exists()
    entry = json.loads((tmp_path / "events.jsonl").read_text().splitlines()[0])
    assert entry["event"] == "alert"
    assert entry["snapshot"] is not None


def test_alert_without_snapshot_still_records(tmp_path):
    events = EventLog(tmp_path / "events.jsonl")
    sec = IntruderDetectionSystem(events=events)

    sec.send_sms_alert()

    assert sec.last_snapshot is None
    entry = json.loads((tmp_path / "events.jsonl").read_text().splitlines()[0])
    assert entry["snapshot"] is None
