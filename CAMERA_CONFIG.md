# Camera Configuration Guide

This document explains how to configure multiple cameras for GPIO privacy button control.

## Configuration File Format

The system uses a JSON configuration file (`cameras_config.json`) to define which cameras to control and their GPIO settings.

### Basic Structure

```json
{
  "cameras": [
    {
      "name": "Camera Name",
      "gpio_pin": 18,
      "led_pin": 24,
      "timeout_minutes": 60,
      "enabled": true,
      "description": "Optional description"
    }
  ],
  "global_settings": {
    "debounce_time": 0.3,
    "polling_interval": 0.1,
    "startup_delay": 5,
    "state_file_path": "/opt/unifi-camera-privacy/privacy_state_example.json"
  }
}
```

## Camera Configuration Fields

### Required Fields

- **`name`**: Exact camera name as it appears in UniFi Protect
- **`gpio_pin`**: GPIO pin number for the button (BCM numbering)
- **`timeout_minutes`**: Minutes before privacy automatically disables

### Optional Fields

- **`led_pin`**: GPIO pin for status LED (omit or set to `null` to disable)
- **`enabled`**: Whether this camera is active (default: `true`)
- **`description`**: Human-readable description for documentation

## Global Settings

- **`debounce_time`**: Button debounce time in seconds (default: 0.3)
- **`polling_interval`**: How often to check buttons/timeouts in seconds (default: 0.1)  
- **`startup_delay`**: Delay before starting in seconds (default: 5)
- **`state_file_path`**: Base path for state files (default: privacy_state_{camera_name}.json)

## GPIO Pin Guidelines

### Pin Numbering
- Uses **BCM (Broadcom) numbering**, not physical pin numbers
- GPIO 18 = BCM 18, not physical pin 18

### Recommended Pins for Buttons/LEDs
- GPIO 16, 18, 19, 20, 21, 26 (good general purpose pins)
- GPIO 22, 23, 24, 25, 27 (also suitable)

### Pins to Avoid
- GPIO 2, 3 (I2C - used by some HATs)
- GPIO 14, 15 (UART - used for serial console)
- GPIO 8, 9, 10, 11 (SPI - used by some HATs)

### Wiring
- **Button**: Connect between GPIO pin and GND (internal pull-up resistor used)
- **LED**: LED anode → GPIO pin, LED cathode → GND (through appropriate resistor)

## Example Configurations

### Single Camera
```json
{
  "cameras": [
    {
      "name": "Bedroom",
      "gpio_pin": 18,
      "led_pin": 24,
      "timeout_minutes": 60,
      "enabled": true
    }
  ]
}
```

### Multiple Cameras
```json
{
  "cameras": [
    {
      "name": "Bedroom",
      "description": "Master bedroom camera",
      "gpio_pin": 18,
      "led_pin": 24,
      "timeout_minutes": 60,
      "enabled": true
    },
    {
      "name": "Living Room", 
      "description": "Main living area",
      "gpio_pin": 19,
      "led_pin": 25,
      "timeout_minutes": 30,
      "enabled": true
    },
    {
      "name": "Kitchen",
      "description": "Kitchen area - no LED",
      "gpio_pin": 20,
      "timeout_minutes": 45,
      "enabled": false
    }
  ]
}
```

### Button Only (No LED)
```json
{
  "cameras": [
    {
      "name": "Hallway",
      "gpio_pin": 21,
      "timeout_minutes": 90,
      "enabled": true
    }
  ]
}
```

## Setup Instructions

1. **Copy the example config**: 
   ```bash
   cp cameras_config.example.json cameras_config.json
   ```

2. **Edit the configuration**:
   ```bash
   nano cameras_config.json
   ```

3. **Update camera names**: Match exactly what appears in UniFi Protect

4. **Set GPIO pins**: Choose appropriate pins for your hardware setup

5. **Configure timeouts**: Set desired auto-disable times in minutes

6. **Test the configuration**:
   ```bash
   python3 gpio_privacy_controller.py
   ```

## State Files

Each camera gets its own state file to track privacy status:
- `privacy_state_{camera_name}.json` 
- Allows state persistence across reboots
- Located in the configured state file directory
- Files are grouped together alphabetically for easier management

## Troubleshooting

### Camera Not Found
- Verify camera name matches exactly (case-sensitive)
- Check UniFi Protect connection
- List available cameras with test script

### GPIO Errors
- Check if pins are already in use
- Verify BCM pin numbering
- Ensure proper wiring (button to GND, LED with resistor)

### Permission Errors  
- Service needs GPIO access
- User must be in `gpio` group
- Check systemd service file configuration

## Advanced Configuration

### Custom Debounce Times
Adjust for different button types:
```json
"global_settings": {
  "debounce_time": 0.5  // Longer for mechanical switches
}
```

### Faster Polling
For more responsive buttons:
```json
"global_settings": {
  "polling_interval": 0.05  // Check every 50ms
}
```

### No Timeout
Disable automatic privacy disable:
```json
{
  "timeout_minutes": 0  // Privacy stays on until manually disabled
}
``` 