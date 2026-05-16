"""
Interactive Mirror with Virtual Assistant Based on Artificial Intelligence
German Patent (Gebrauchsmuster) DE 20 2023 105 343
IPC: G08B 13/196 (Alarm systems using infrared)

Features:
- AI-based voice assistant
- PIR sensor + GSM module for theft/intruder detection
- IR frame for touch capabilities
- Built with Python, OpenCV, JavaScript
- Total cost: ~$500 (vs market $5k-$8k)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

PATENT_ID = "DE 20 2023 105 343"
PATENT_IPC = "G08B 13/196"
DEFAULT_OWNER_PHONE = "+918050477475"

log = logging.getLogger("mirror")


# ─── Mock hardware libraries for the portfolio demo ───────────────────────────
class MockGPIO:
    IN = "IN"
    OUT = "OUT"
    HIGH = 1
    LOW = 0
    BCM = "BCM"

    def __init__(self, motion_probability: float = 0.05) -> None:
        self._motion_probability = motion_probability

    def setmode(self, mode: str) -> None:
        pass

    def setup(self, pin: int, mode: str) -> None:
        pass

    def input(self, pin: int) -> int:
        return self.HIGH if random.random() < self._motion_probability else self.LOW


class MockSerial:
    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        self.port = port

    def write(self, data: bytes) -> None:
        log.info("[GSM TX] %s", data.decode(errors="replace").strip())

    def readline(self) -> bytes:
        return b"OK\r\n"


# ─── Event log (JSON lines) ───────────────────────────────────────────────────
class EventLog:
    """Append-only JSON-lines log of security events for audit."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record(self, event: str, **payload: object) -> dict:
        entry = {
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "event": event,
            **payload,
        }
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        return entry


# ─── Voice assistant ──────────────────────────────────────────────────────────
COMMAND_MAP: dict[str, str] = {
    "arm security": "ARM_SECURITY",
    "lock down": "ARM_SECURITY",
    "disarm": "DISARM_SECURITY",
    "weather": "SHOW_WEATHER",
}


def parse_command(text: str) -> str:
    lowered = text.lower()
    for keyword, action in COMMAND_MAP.items():
        if keyword in lowered:
            return action
    return "UNKNOWN"


# ─── Hardware Integration (Patent Specifics) ──────────────────────────────────
class IntruderDetectionSystem:
    """
    IPC G08B 13/196: Alarm systems using infrared.
    PIR sensor for motion detection + GSM module for SMS alerts.
    """

    def __init__(
        self,
        pir_pin: int = 4,
        serial_port: str = "/dev/ttyS0",
        owner_phone: str = DEFAULT_OWNER_PHONE,
        alert_cooldown: float = 10.0,
        events: EventLog | None = None,
    ) -> None:
        self.pir_pin = pir_pin
        self.owner_phone = owner_phone
        self.alert_cooldown = alert_cooldown
        self.events = events

        self.gpio = MockGPIO()
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.pir_pin, self.gpio.IN)

        self.gsm = MockSerial(serial_port, baudrate=9600, timeout=1)

        self._armed = threading.Event()
        self._stop = threading.Event()
        self._last_alert: float = 0.0
        self._thread: threading.Thread | None = None

    @property
    def armed(self) -> bool:
        return self._armed.is_set()

    def arm(self) -> None:
        self._armed.set()
        log.info("[Security] armed — PIR active")
        if self.events:
            self.events.record("armed")

    def disarm(self) -> None:
        self._armed.clear()
        log.info("[Security] disarmed")
        if self.events:
            self.events.record("disarmed")

    def send_sms_alert(self) -> None:
        """Send SMS via GSM module AT commands."""
        log.warning(
            "[Security] motion detected while armed — SMS to %s", self.owner_phone
        )
        self.gsm.write(b"AT+CMGF=1\r")
        self.gsm.write(f'AT+CMGS="{self.owner_phone}"\r'.encode())
        self.gsm.write(b"ALERT: Motion detected by Smart Mirror security system.\x1a")
        self._last_alert = time.monotonic()
        if self.events:
            self.events.record("alert", phone=self.owner_phone)

    def _monitor(self, poll_interval: float) -> None:
        while not self._stop.is_set():
            if (
                self._armed.is_set()
                and self.gpio.input(self.pir_pin) == self.gpio.HIGH
                and time.monotonic() - self._last_alert >= self.alert_cooldown
            ):
                self.send_sms_alert()
            self._stop.wait(poll_interval)

    def start_monitor(self, poll_interval: float = 0.5) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._monitor, args=(poll_interval,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)


# ─── UI ───────────────────────────────────────────────────────────────────────
@dataclass
class MirrorState:
    security_armed: bool = False
    current_view: str = "home"


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in ("DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


class SmartMirrorUI:
    """Renders the UI for the IR touch frame display."""

    def __init__(self, size: tuple[int, int] = (1080, 1920)) -> None:
        self.size = size
        self._font_time = _load_font(96)
        self._font_date = _load_font(36)
        self._font_status = _load_font(48)
        self._font_footer = _load_font(20)

    def render(self, state: MirrorState, output_path: str | Path) -> Path:
        img = Image.new("RGB", self.size, color=(0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.text((50, 50), time.strftime("%H:%M"), fill=(255, 255, 255), font=self._font_time)
        draw.text((50, 170), time.strftime("%A, %B %d"), fill=(180, 180, 180), font=self._font_date)

        sec_color = (255, 50, 50) if state.security_armed else (50, 255, 50)
        sec_text = "SYSTEM ARMED (PIR ACTIVE)" if state.security_armed else "SYSTEM DISARMED"
        draw.text((50, 260), f"Security: {sec_text}", fill=sec_color, font=self._font_status)

        draw.text(
            (50, 1800),
            f"Patent {PATENT_ID} | Ashish Shetty",
            fill=(100, 100, 100),
            font=self._font_footer,
        )
        draw.text(
            (50, 1840),
            f"IPC: {PATENT_IPC}",
            fill=(100, 100, 100),
            font=self._font_footer,
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        return output_path


# ─── Main application ─────────────────────────────────────────────────────────
class InteractiveMirror:
    def __init__(
        self,
        owner_phone: str = DEFAULT_OWNER_PHONE,
        output_dir: Path = Path("outputs"),
    ) -> None:
        self.output_dir = Path(output_dir)
        self.events = EventLog(self.output_dir / "events.jsonl")
        self.security = IntruderDetectionSystem(owner_phone=owner_phone, events=self.events)
        self.ui = SmartMirrorUI()
        self.state = MirrorState()

    def handle(self, text: str) -> str:
        action = parse_command(text)
        if action == "ARM_SECURITY":
            self.security.arm()
            self.state.security_armed = True
        elif action == "DISARM_SECURITY":
            self.security.disarm()
            self.state.security_armed = False
        return action

    def run_demo(self, output_dir: Path) -> None:
        log.info("=" * 60)
        log.info("INTERACTIVE MIRROR WITH VIRTUAL ASSISTANT")
        log.info("Patent: %s (Gebrauchsmuster) — IPC %s", PATENT_ID, PATENT_IPC)
        log.info("Cost: ~$500 (RPi, IR Frame, PIR, GSM)")
        log.info("=" * 60)

        self.ui.render(self.state, output_dir / "mirror_ui_disarmed.png")

        log.info("[User] 'Hey mirror, arm security'")
        self.handle("arm security")
        self.ui.render(self.state, output_dir / "mirror_ui_armed.png")

        log.info("[Hardware] PIR sensor triggered by movement")
        self.security.send_sms_alert()

        log.info("Demo complete — UI renders saved to %s", output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smart Mirror portfolio demo.")
    parser.add_argument(
        "--phone",
        default=os.environ.get("MIRROR_OWNER_PHONE", DEFAULT_OWNER_PHONE),
        help="Phone number for SMS alerts (env: MIRROR_OWNER_PHONE).",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("outputs"),
        type=Path,
        help="Where to save the rendered UI PNGs.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level, format="%(message)s")

    mirror = InteractiveMirror(owner_phone=args.phone, output_dir=args.output_dir)
    mirror.run_demo(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
