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
import time
import json
import os
import threading
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

# Mock hardware libraries for the portfolio demo
class MockGPIO:
    IN = "IN"
    OUT = "OUT"
    HIGH = 1
    LOW = 0
    BCM = "BCM"
    def setmode(self, mode): pass
    def setup(self, pin, mode): pass
    def input(self, pin): 
        # Simulate occasional motion detection
        return np.random.random() < 0.05

class MockSerial:
    def __init__(self, port, baudrate, timeout): pass
    def write(self, data): print(f"[GSM Module] TX: {data.decode().strip()}")
    def readline(self): return b"OK\r\n"

# ─── Hardware Integration (Patent Specifics) ──────────────────────────────────
class IntruderDetectionSystem:
    """
    IPC G08B 13/196: Alarm systems using infrared.
    Integrates PIR sensor for motion detection and GSM module for SMS alerts.
    """
    def __init__(self, pir_pin=4, serial_port='/dev/ttyS0'):
        self.pir_pin = pir_pin
        self.gpio = MockGPIO()
        self.gpio.setmode(self.gpio.BCM)
        self.gpio.setup(self.pir_pin, self.gpio.IN)
        
        self.gsm = MockSerial(serial_port, baudrate=9600, timeout=1)
        self.armed = False
        self.owner_phone = "+918050477475" # From resume
        
    def arm_system(self):
        print("[Security] Intruder detection armed (PIR active)")
        self.armed = True
        
    def disarm_system(self):
        print("[Security] Intruder detection disarmed")
        self.armed = False
        
    def send_sms_alert(self):
        """Send SMS via GSM module AT commands."""
        print(f"[Security] WARNING: Motion detected while armed! Sending SMS to {self.owner_phone}...")
        self.gsm.write(b"AT+CMGF=1\r") # Text mode
        time.sleep(0.1)
        self.gsm.write(f"AT+CMGS=\"{self.owner_phone}\"\r".encode())
        time.sleep(0.1)
        self.gsm.write(b"ALERT: Motion detected by Smart Mirror security system.\x1A")
        
    def monitor_loop(self):
        """Background thread monitoring the PIR sensor."""
        while True:
            if self.armed and self.gpio.input(self.pir_pin) == self.gpio.HIGH:
                self.send_sms_alert()
                time.sleep(10) # Cooldown
            time.sleep(0.5)


# ─── AI Components ────────────────────────────────────────────────────────────
class VoiceAssistant:
    """On-device wake word and voice command processing."""
    def __init__(self):
        self.is_listening = False
        
    def process_command(self, command):
        cmd = command.lower()
        if "arm security" in cmd or "lock down" in cmd:
            return "ARM_SECURITY"
        elif "disarm" in cmd:
            return "DISARM_SECURITY"
        elif "weather" in cmd:
            return "SHOW_WEATHER"
        return "UNKNOWN"

class SmartMirrorUI:
    """Renders the UI for the IR touch frame display."""
    def __init__(self, size=(1080, 1920)):
        self.size = size
        
    def render(self, state, output_path="outputs/mirror_ui.png"):
        img = Image.new('RGB', self.size, color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Header
        draw.text((50, 50), time.strftime("%H:%M"), fill=(255, 255, 255))
        draw.text((50, 100), time.strftime("%A, %B %d"), fill=(180, 180, 180))
        
        # Security Status (The patented feature)
        sec_color = (255, 50, 50) if state['security_armed'] else (50, 255, 50)
        sec_text = "SYSTEM ARMED (PIR ACTIVE)" if state['security_armed'] else "SYSTEM DISARMED"
        draw.text((50, 200), f"Security: {sec_text}", fill=sec_color)
        
        # Patent Info
        draw.text((50, 1800), "Patent DE 20 2023 105 343 | Ashish Shetty", fill=(100, 100, 100))
        draw.text((50, 1830), "IPC: G08B 13/196", fill=(100, 100, 100))
        
        os.makedirs('outputs', exist_ok=True)
        img.save(output_path)
        return output_path

# ─── Main Application ─────────────────────────────────────────────────────────
class InteractiveMirror:
    def __init__(self):
        self.security = IntruderDetectionSystem()
        self.assistant = VoiceAssistant()
        self.ui = SmartMirrorUI()
        self.state = {
            "security_armed": False,
            "current_view": "home"
        }
        
    def start(self):
        print("=" * 60)
        print("INTERACTIVE MIRROR WITH VIRTUAL ASSISTANT")
        print("Patent: DE 20 2023 105 343 (Gebrauchsmuster)")
        print("Cost: ~$500 (Hardware: RPi, IR Frame, PIR, GSM)")
        print("=" * 60)
        
        # Start security monitor thread
        monitor_thread = threading.Thread(target=self.security.monitor_loop, daemon=True)
        monitor_thread.start()
        
        # Simulate a sequence of events
        self.ui.render(self.state, "outputs/mirror_ui_disarmed.png")
        
        print("\n[User] 'Hey mirror, arm security'")
        cmd = self.assistant.process_command("arm security")
        if cmd == "ARM_SECURITY":
            self.security.arm_system()
            self.state['security_armed'] = True
            self.ui.render(self.state, "outputs/mirror_ui_armed.png")
            
        print("\n[System] Simulating house empty...")
        time.sleep(2)
        
        print("\n[Hardware] PIR sensor triggered by movement!")
        # The background thread would catch this, but we force it for the demo output
        self.security.send_sms_alert()
        
        print("\nDemo complete. UI renders saved to outputs/")

if __name__ == "__main__":
    mirror = InteractiveMirror()
    mirror.start()
