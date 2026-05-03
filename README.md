# ai-smart-mirror

This is the project that got me a German patent. Built it for my major project in college between Jan 2022 and June 2023.

Patent: DE 20 2023 105 343 (Gebrauchsmuster), IPC: G08B 13/196

It's a smart mirror but instead of just showing the weather, I built it as a full home security system. The core feature that got patented is the integration of an AI voice assistant with a hardware-level intruder detection system.

I wired up a PIR (Passive Infrared) sensor and a GSM module directly to the Raspberry Pi. When you tell the mirror to "arm security" before leaving the house, it activates the PIR sensor. If motion is detected while armed, the GSM module immediately fires off an SMS alert to my phone using AT commands over serial.

I also added an IR frame around the glass to give it touch capabilities without needing an expensive capacitive touch display. The whole thing cost about $500 to build. Commercial smart mirrors with security features usually run $5,000 to $8,000.

The research paper got published on ResearchSquare and ResearchGate and was accepted by multiple IEEE conferences.

```bash
pip install numpy Pillow opencv-python-headless
python mirror_core.py
```

The script runs a software simulation of the hardware components. GPIO for the PIR sensor and Serial for the GSM module are mocked so you can run it without the physical hardware. It simulates the arming process, triggers a motion event, and outputs the simulated AT commands that would be sent to the GSM module.
