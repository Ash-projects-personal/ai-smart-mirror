# ai-smart-mirror

This is the project that got me a German patent (Gebrauchsmuster). Built it for my major project in college between Jan 2022 and June 2023.

## What this does

It's a smart mirror, but instead of just showing the weather, I built it as a full home security system. The core feature that got patented is the integration of an AI voice assistant with a hardware-level intruder detection system.

I wired up a PIR (Passive Infrared) sensor and a GSM module directly to the Raspberry Pi. When you tell the mirror to "arm security" before leaving the house, it activates the PIR sensor. If motion is detected while armed, the GSM module immediately fires off an SMS alert to my phone. 

I also added an IR frame around the glass to give it touch capabilities without needing an expensive capacitive touch display.

## The numbers and recognition

- **Patent**: German Patent DE 20 2023 105 343 (IPC: G08B 13/196 - Alarm systems using infrared)
- **Cost**: Built the whole thing for about $500. Commercial smart mirrors with security features usually run $5,000-$8,000.
- **Publications**: Published the research paper on ResearchSquare and ResearchGate, and it got accepted by multiple IEEE conferences.

## How to run

```bash
pip install numpy Pillow opencv-python-headless
python mirror_core.py
```

The script runs a software simulation of the hardware components (GPIO for the PIR sensor, Serial for the GSM module). It simulates the arming process, triggers a motion event, and outputs the simulated AT commands that would be sent to the GSM module to trigger the SMS.

## Files

- `mirror_core.py`: The main system logic handling GPIO, Serial communication, and the UI rendering.
- `outputs/mirror_ui_disarmed.png`: Simulated display state
- `outputs/mirror_ui_armed.png`: Simulated display state when PIR is active
