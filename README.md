# UniFi Protect Camera Privacy Zone Manager

A Python application that allows you to toggle privacy zones for UniFi Protect cameras. This tool provides both command-line and interactive interfaces for managing camera privacy settings.

## Features

- 🔒 Toggle privacy zones on/off for UniFi Protect cameras
- 💡 **LED Control**: Turn camera LED off/on for visual privacy indication
- 📋 List all cameras with their current privacy and LED status
- 🖥️ Interactive mode for easy camera management
- ⚡ Command-line interface for automation and scripting
- 🎨 Colorized output for better visibility
- 🔧 Flexible configuration via environment variables or CLI arguments

## Requirements

- Python 3.10 or higher
- UniFi Protect version 1.20+
- A local user account on your UniFi Protect system (Ubiquiti SSO accounts are not supported)

## Installation

### Standard Installation

1. **Clone or download this repository:**
   ```bash
   git clone <repository-url>
   cd unifi_camera_management
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make the script executable (optional):**
   ```bash
   chmod +x unifi_camera_privacy.py
   ```

### Raspberry Pi GPIO Button Installation

For Raspberry Pi users who want GPIO button control with auto-disable timeout:

1. **Clone or copy the project files to your Raspberry Pi**
2. **Run the automated setup script:**
   ```bash
   chmod +x setup_rpi.sh
   ./setup_rpi.sh
   ```
3. **Configure your UniFi Protect settings:**
   ```bash
   sudo nano /opt/unifi-camera-privacy/.env
   ```
4. **Test the connection:**
   ```bash
   cd /opt/unifi-camera-privacy
   ./venv/bin/python test_connection.py
   ```
5. **Test GPIO hardware:**
   ```bash
   cd /opt/unifi-camera-privacy
   ./venv/bin/python test_gpio.py
   ```
6. **Start the service:**
   ```bash
   sudo systemctl start privacy-button
   sudo systemctl status privacy-button
   ```

The Raspberry Pi setup includes:
- 🔘 **GPIO Button Control**: Physical button on GPIO 18 to toggle privacy
- ⏰ **60-minute Auto-disable**: Privacy automatically turns off after 1 hour
- 💡 **LED Indicator**: Visual feedback on GPIO 24
- 🔄 **System Service**: Runs automatically on boot
- 📊 **Logging**: Full systemd integration with journalctl

## Configuration

### Option 1: Environment Variables

1. **Copy the example configuration file:**
   ```bash
   cp config.env.example .env
   ```

2. **Edit the `.env` file with your UniFi Protect details:**
   ```bash
   # UniFi Protect Configuration
   UFP_HOST=192.168.1.1
   UFP_PORT=443
   UFP_USERNAME=your_username
   UFP_PASSWORD=your_password
   UFP_SSL_VERIFY=True
   
   # Optional: Timezone (defaults to system timezone)
   TZ=America/New_York
   ```

### Option 2: Command Line Arguments

You can also provide configuration directly via command line arguments (see usage examples below).

## Usage

### Interactive Mode (Recommended for beginners)

Run the application in interactive mode to easily manage your cameras:

```bash
python unifi_camera_privacy.py --interactive
```

Or simply:
```bash
python unifi_camera_privacy.py
```

This will show you a menu with all your cameras and their current privacy status, allowing you to toggle them easily.

### Command Line Interface

#### List all cameras:
```bash
python unifi_camera_privacy.py --list
```

#### Toggle privacy zone for a specific camera:
```bash
python unifi_camera_privacy.py --camera "Front Door Camera"
```

#### Enable privacy mode for a camera:
```bash
python unifi_camera_privacy.py --camera "Front Door Camera" --enable-privacy
```

#### Disable privacy mode for a camera:
```bash
python unifi_camera_privacy.py --camera "Front Door Camera" --disable-privacy
```

#### Using command line arguments for connection:
```bash
python unifi_camera_privacy.py \
  --host 192.168.1.100 \
  --username admin \
  --password mypassword \
  --camera "Garage Camera" \
  --enable-privacy
```

### Advanced Usage

#### Disable SSL verification (for self-signed certificates):
```bash
python unifi_camera_privacy.py --no-ssl-verify --list
```

#### Using camera ID instead of name:
```bash
python unifi_camera_privacy.py --camera "61b3f5c7033ea703e7000424"
```

#### LED Control Commands:

```bash
# Turn off LED (good for privacy indication)
python unifi_camera_privacy.py --camera "Front Door Camera" --led-off

# Turn on LED (restore normal operation)
python unifi_camera_privacy.py --camera "Front Door Camera" --led-on

# Check LED status
python unifi_camera_privacy.py --camera "Front Door Camera" --led-status
```

#### IR LED Control Commands:

```bash
# Turn off IR LEDs (enhanced privacy - no night vision)
python unifi_camera_privacy.py --camera "Front Door Camera" --ir-off

# Set IR LEDs to auto mode (restore normal night vision)
python unifi_camera_privacy.py --camera "Front Door Camera" --ir-auto

# Check IR LED status
python unifi_camera_privacy.py --camera "Front Door Camera" --ir-status
```

## How Privacy Zones Work

When you enable a privacy zone:
- 🔒 A privacy zone covering the entire camera view is created
- 📹 The camera continues recording but the view is blocked
- 🚫 Motion detection may be disabled (depending on UniFi Protect settings)
- 💡 **Status LED is turned OFF** (visual privacy indicator)
- 🌙 **IR LEDs are turned OFF** (enhanced privacy - no night vision)

When you disable a privacy zone:
- ✅ All privacy zones are removed from the camera
- 👁️ The camera view is restored to normal
- 📹 Recording and motion detection resume normal operation
- 💡 **Status LED is restored to normal** (visual confirmation)
- 🌙 **IR LEDs are restored to AUTO** (night vision restored)

## LED & IR Control Features

The application now includes comprehensive lighting control for supported cameras:

### Automatic Control (Privacy Mode):
- 🔴 **Privacy Mode ON**: Status LED turns OFF, IR LEDs turn OFF
- 🟢 **Privacy Mode OFF**: Status LED turns ON, IR LEDs return to AUTO
- 👁️ **Visual Feedback**: Instantly see privacy status from across the room
- 🌙 **Enhanced Privacy**: No night vision recording when privacy enabled

### Manual LED Control:
- 🎛️ **Independent Control**: Turn status LED on/off without affecting privacy zones
- 🔍 **Status Check**: Query current LED state
- 🏠 **Home Automation**: Perfect for smart home integrations

### Manual IR LED Control:
- 🌙 **Night Vision Control**: Turn IR LEDs off/auto independently
- 🔍 **Status Check**: Query current IR LED mode (OFF/AUTO/ON/etc.)
- 🔒 **Enhanced Privacy**: Disable night vision without privacy zones
- 🏠 **Automation Ready**: Perfect for scheduled privacy modes

## Security Considerations

- 🔐 Use a dedicated local user account (not your main admin account)
- 🏠 Only use this tool on your local network
- 🔒 Keep your `.env` file secure and never commit it to version control
- 🚫 Ubiquiti SSO accounts are not supported for security reasons

## Troubleshooting

### Connection Issues

**Problem:** "Failed to connect to UniFi Protect"
- ✅ Verify your host IP address and port
- ✅ Ensure your username and password are correct
- ✅ Check if you're using a local user account (not SSO)
- ✅ Try disabling SSL verification with `--no-ssl-verify`

### Camera Not Found

**Problem:** "Camera 'Name' not found"
- ✅ Use `--list` to see all available cameras
- ✅ Check camera name spelling (case-insensitive)
- ✅ Try using the camera ID instead of name

### Permission Issues

**Problem:** "Failed to toggle privacy zone"
- ✅ Ensure your user has camera management permissions
- ✅ Check if the camera is online and responsive
- ✅ Try updating UniFi Protect to the latest version

## Examples

### Automation Script Example

Create a simple script to toggle privacy for multiple cameras:

```bash
#!/bin/bash
# toggle_cameras.sh

echo "Enabling privacy for all outdoor cameras..."
python unifi_camera_privacy.py --camera "Front Door" --enable-privacy
python unifi_camera_privacy.py --camera "Backyard" --enable-privacy
python unifi_camera_privacy.py --camera "Driveway" --enable-privacy

echo "Privacy enabled for outdoor cameras!"
```

### Home Assistant Integration

You can integrate this script with Home Assistant using the `shell_command` integration:

```yaml
# configuration.yaml
shell_command:
  enable_camera_privacy: 'python /path/to/unifi_camera_privacy.py --camera "{{ camera_name }}" --enable-privacy'
  disable_camera_privacy: 'python /path/to/unifi_camera_privacy.py --camera "{{ camera_name }}" --disable-privacy'
```

## Command Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--host` | `-h` | UniFi Protect host address |
| `--port` | `-p` | UniFi Protect port (default: 443) |
| `--username` | `-u` | UniFi Protect username |
| `--password` | `-w` | UniFi Protect password |
| `--no-ssl-verify` | | Disable SSL certificate verification |
| `--camera` | `-c` | Camera name or ID to operate on |
| `--list` | | List all cameras and their privacy status |
| `--enable-privacy` | | Enable privacy mode for specified camera |
| `--disable-privacy` | | Disable privacy mode for specified camera |
| `--led-off` | | Turn off LED for specified camera |
| `--led-on` | | Turn on LED for specified camera |
| `--led-status` | | Show LED status for specified camera |
| `--ir-off` | | Turn off IR LEDs for specified camera |
| `--ir-auto` | | Set IR LEDs to auto mode for specified camera |
| `--ir-status` | | Show IR LED status for specified camera |
| `--interactive` | `-i` | Run in interactive mode |

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is an unofficial tool for UniFi Protect. There is no affiliation with Ubiquiti. Use at your own risk.

---

**Note:** Always test this tool in a safe environment before using it in production. Privacy zones are an important security feature, so make sure you understand how they work before automating their control. 