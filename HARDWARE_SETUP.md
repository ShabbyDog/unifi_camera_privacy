# Hardware Setup Guide

## Raspberry Pi GPIO Privacy Button Controller

### Required Components

- **Raspberry Pi** (any model with GPIO pins)
- **Momentary Push Button** (normally open)
- **LED** (optional, for status indication)
- **220Ω Resistor** (for LED)
- **Jumper wires**
- **Breadboard** (optional, for prototyping)

### Wiring Diagram

```
Raspberry Pi GPIO Pinout (relevant pins):

    3V3  (1) (2)  5V
  GPIO2  (3) (4)  5V
  GPIO3  (5) (6)  GND
  GPIO4  (7) (8)  GPIO14
    GND  (9) (10) GPIO15
 GPIO17 (11) (12) GPIO18  ← BUTTON
 GPIO27 (13) (14) GND     ← BUTTON GND
 GPIO22 (15) (16) GPIO23
    3V3 (17) (18) GPIO24  ← LED
 GPIO10 (19) (20) GND     ← LED GND
```

### Button Wiring

```
GPIO 18 ──────┐
              │
              ├── Button ── GND
              │
         (Pull-up resistor
          built-in to Pi)
```

**Pin Connections:**
- **Button Pin 1** → **GPIO 18** (Physical pin 12)
- **Button Pin 2** → **GND** (Physical pin 14)

### LED Wiring (Optional)

```
GPIO 24 ────── 220Ω Resistor ────── LED (+) ────── LED (-) ────── GND
```

**Pin Connections:**
- **GPIO 24** (Physical pin 18) → **220Ω Resistor** → **LED Anode (+)**
- **LED Cathode (-)** → **GND** (Physical pin 20)

### Physical Pin Layout

```
RASPBERRY PI GPIO HEADER
┌─────────────────────────────┐
│ 3V3    (1)  (2)    5V       │
│ GPIO2  (3)  (4)    5V       │
│ GPIO3  (5)  (6)    GND      │
│ GPIO4  (7)  (8)    GPIO14   │
│ GND    (9)  (10)   GPIO15   │
│ GPIO17 (11) (12)   GPIO18 ← │ BUTTON
│ GPIO27 (13) (14)   GND ←   │ BUTTON GND
│ GPIO22 (15) (16)   GPIO23   │
│ 3V3    (17) (18)   GPIO24 ← │ LED
│ GPIO10 (19) (20)   GND ←   │ LED GND
└─────────────────────────────┘
```

### LED Behavior

- **LED ON** (GPIO HIGH): Privacy mode **DISABLED** - camera is **active**
- **LED OFF** (GPIO LOW): Privacy mode **ENABLED** - camera has **privacy zone**

### Button Behavior

- **First Press**: Enable privacy mode (LED turns OFF, camera privacy ON)
- **Second Press**: Disable privacy mode (LED turns ON, camera privacy OFF)
- **Timeout**: After 60 minutes, privacy automatically turns OFF (LED turns ON)

### Safety Notes

⚠️ **Important Safety Guidelines:**

1. **Power Off**: Always power off the Raspberry Pi before making connections
2. **Correct Orientation**: Ensure LED polarity is correct (longer leg = positive)
3. **Resistor Required**: Always use a resistor with the LED to prevent damage
4. **GPIO Limits**: Don't exceed 3.3V on GPIO pins
5. **Current Limits**: GPIO pins can only source ~16mA safely

### Troubleshooting

#### Button Not Working
- Check button connections
- Ensure button is normally open (NO) type
- Test with multimeter for continuity
- Verify GPIO pin number in code

#### LED Not Working
- Check LED polarity (swap if needed)
- Verify resistor value (220Ω recommended)
- Test LED with 3.3V directly
- Check GPIO pin connections

#### Permission Issues
- Add user to gpio group: `sudo usermod -a -G gpio $USER`
- Log out and log back in
- Check service permissions

### Optional: PCB Design

For a permanent installation, consider creating a simple PCB with:

```
[Raspberry Pi Header] ── [Button] ── [LED + Resistor] ── [Screw Terminals]
```

### Enclosure Ideas

- **3D Printed Case**: Custom design with button cutout
- **Project Box**: Standard electronics enclosure
- **Wall Mount**: For bedroom installation
- **Desk Mount**: For easy access

### Advanced Features (Future)

- **Multiple Buttons**: Control different cameras
- **RGB LED**: Different colors for different states
- **Buzzer**: Audio feedback for button presses
- **OLED Display**: Show camera status and timer
- **PIR Sensor**: Auto-enable privacy when motion detected

---

## Quick Setup Commands

```bash
# Copy files to Raspberry Pi
scp -r unifi_camera_management/ pi@your-pi-ip:/home/pi/

# SSH to Pi and run setup
ssh pi@your-pi-ip
cd /home/pi/unifi_camera_management
chmod +x setup_rpi.sh
./setup_rpi.sh
```

That's it! Your privacy button controller is ready to use! 🎉 