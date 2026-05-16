# ai-smart-mirror


> **Patent:** German utility model (Gebrauchsmuster) **DE 20 2023 105 343**, IPC `G08B 13/196` — issued 2023. The AI voice assistant + hardware intruder-detection integration described in this repo is covered by that filing.
This is the project that got me a German patent. Built it for my major project in college between Jan 2022 and June 2023.

Patent: DE 20 2023 105 343 (Gebrauchsmuster), IPC: G08B 13/196

It's a smart mirror but instead of just showing the weather, I built it as a full home security system. The core feature that got patented is the integration of an AI voice assistant with a hardware-level intruder detection system.

I wired up a PIR (Passive Infrared) sensor and a GSM module directly to the Raspberry Pi. When you tell the mirror to "arm security" before leaving the house, it activates the PIR sensor. If motion is detected while armed, the GSM module immediately fires off an SMS alert to my phone using AT commands over serial.

I also added an IR frame around the glass to give it touch capabilities without needing an expensive capacitive touch display. The whole thing cost about $500 to build. Commercial smart mirrors with security features usually run $5,000 to $8,000.

The research paper got published on ResearchSquare and ResearchGate and was accepted by multiple IEEE conferences.

```bash
pip install -r requirements.txt
python mirror_core.py                            # scripted demo
python mirror_core.py --interactive              # REPL: type commands on stdin
python mirror_core.py --weather-seed 42 --user ashish
```

The script runs a software simulation of the hardware components. GPIO for the PIR sensor and Serial for the GSM module are mocked so you can run it without the physical hardware.

### Features in the demo

- **Voice command parser** with optional `hey mirror` wake-word: `arm security`, `disarm`, `weather`, `who am i`, `snapshot`, `quit`
- **Intruder detection** — armed PIR triggers a GSM `AT+CMGS` SMS to the owner phone (env var `MIRROR_OWNER_PHONE`)
- **Snapshot capture** — every alert renders a timestamped PNG to `outputs/snapshots/` and the filename is appended to the SMS body
- **JSON-lines audit log** at `outputs/events.jsonl` (thread-safe append) for `armed`, `disarmed`, `alert` events
- **Weather widget** with a seeded stub provider (swap for OpenWeatherMap in production) rendered on the mirror UI
- **Face-recognition stub** — `--user ashish|guest` selects a `UserProfile` and the greeting renders on the mirror
- **TrueType font rendering** at 1080×1920 with a graceful fallback to PIL's default

### Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

CI runs on push and PR across Python 3.10/3.11/3.12 — see `.github/workflows/ci.yml`.
