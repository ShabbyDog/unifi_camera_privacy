#!/usr/bin/env python3
"""
Raspberry Pi GPIO Privacy Button Controller

Hardware button controller for UniFi Protect camera privacy zones.
- Multiple camera support with individual GPIO pins
- Configurable timeouts per camera
- Auto-disable: Privacy automatically turns off after specified timeout
- LED feedback: Optional LED indicators for privacy status
"""

import asyncio
import json
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("RPi.GPIO not available. Install with: pip install RPi.GPIO")
    print("Note: This only works on Raspberry Pi hardware")
    sys.exit(1)

from colorama import init, Fore, Style
from dotenv import load_dotenv

# Import our existing UniFi Protect manager
from unifi_camera_privacy import UniFiProtectManager, load_config

# Initialize colorama
init(autoreset=True)

def load_cameras_config(config_file: str = "cameras_config.json") -> Dict:
    """Load camera configuration from JSON file."""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"{Fore.RED}✗ Camera config file not found: {config_file}")
        print(f"{Fore.CYAN}Please create {config_file} with your camera definitions")
        sys.exit(1)
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'cameras' not in config:
            raise ValueError("Config file must contain 'cameras' array")
        
        print(f"{Fore.GREEN}✓ Loaded camera config from {config_file}")
        enabled_cameras = [cam for cam in config['cameras'] if cam.get('enabled', True)]
        print(f"{Fore.CYAN}  Found {len(enabled_cameras)} enabled cameras")
        
        return config
    
    except json.JSONDecodeError as e:
        print(f"{Fore.RED}✗ Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to load config: {e}")
        sys.exit(1)

class PrivacyButtonController:
    """GPIO button controller for camera privacy."""
    
    def __init__(self, camera_name: str, button_pin: int = 18, led_pin: Optional[int] = 24, 
                 timeout_minutes: int = 60):
        """
        Initialize the privacy button controller.
        
        Args:
            camera_name: Name of the camera to control
            button_pin: GPIO pin number for the button (BCM numbering)
            led_pin: GPIO pin number for status LED (BCM numbering, optional)
            timeout_minutes: Minutes before auto-disable privacy (default: 60)
        """
        self.camera_name = camera_name
        self.button_pin = button_pin
        self.led_pin = led_pin
        self.timeout_minutes = timeout_minutes
        
        # State management
        self.privacy_enabled = False
        self.privacy_start_time: Optional[datetime] = None
        self.last_button_press = 0
        self.debounce_time = 0.3  # 300ms debounce
        
        # UniFi Protect manager
        self.manager: Optional[UniFiProtectManager] = None
        
        # Control flags
        self.running = True
        self.state_file = Path(f"/opt/unifi-camera-privacy/privacy_state_{camera_name}.json")
        
        print(f"{Fore.CYAN}Privacy Button Controller initialized:")
        print(f"  Camera: {camera_name}")
        print(f"  Button Pin: GPIO {button_pin}")
        print(f"  LED Pin: GPIO {led_pin}" if led_pin else "  LED Pin: None")
        print(f"  Timeout: {timeout_minutes} minutes")
    
    def setup_gpio(self):
        """Set up GPIO pins."""
        # Disable GPIO warnings for cleaner output
        GPIO.setwarnings(False)
        
        # Clean up any existing GPIO state
        GPIO.cleanup()
        
        GPIO.setmode(GPIO.BCM)
        
        try:
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"{Fore.GREEN}✓ Button GPIO {self.button_pin} setup successful")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to setup button GPIO {self.button_pin}: {e}")
            raise
        
        if self.led_pin:
            try:
                GPIO.setup(self.led_pin, GPIO.OUT)
                GPIO.output(self.led_pin, GPIO.LOW)
                print(f"{Fore.GREEN}✓ LED GPIO {self.led_pin} setup successful")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠ LED GPIO {self.led_pin} setup failed: {e}")
                self.led_pin = None  # Disable LED if it can't be set up
        
        # Set up button interrupt
        try:
            GPIO.add_event_detect(self.button_pin, GPIO.FALLING, 
                                 callback=self.button_callback, bouncetime=200)
            print(f"{Fore.GREEN}✓ Button interrupt setup successful")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to setup button interrupt: {e}")
            print(f"{Fore.YELLOW}  Will use polling mode only")
            # Don't raise here - polling backup will work
        
        print(f"{Fore.GREEN}✓ GPIO setup complete")
        print(f"{Fore.CYAN}  Button: GPIO {self.button_pin} (falling edge detection)")
        print(f"{Fore.CYAN}  LED: GPIO {self.led_pin}" if self.led_pin else f"{Fore.YELLOW}  LED: Disabled")
    
    def button_callback(self, channel):
        """Handle button press with debouncing."""
        current_time = time.time()
        
        print(f"{Fore.CYAN}🔘 Button callback triggered on GPIO {channel}")
        
        # Debounce check
        if current_time - self.last_button_press < self.debounce_time:
            print(f"{Fore.YELLOW}  ⏱️ Debounced (too soon)")
            return
        
        self.last_button_press = current_time
        print(f"{Fore.GREEN}  ✓ Button press accepted")
        
        # Queue the async button handler
        try:
            asyncio.create_task(self.handle_button_press())
            print(f"{Fore.CYAN}  📋 Async task queued")
        except Exception as e:
            print(f"{Fore.RED}  ✗ Failed to queue async task: {e}")
    
    async def handle_button_press(self):
        """Handle button press async operations."""
        print(f"{Fore.BLUE}🔄 Processing button press...")
        try:
            if self.privacy_enabled:
                # Privacy is on, turn it off
                print(f"{Fore.CYAN}  Current state: Privacy ON, disabling...")
                await self.disable_privacy()
                print(f"{Fore.GREEN}🔘 Button pressed - Privacy DISABLED")
            else:
                # Privacy is off, turn it on
                print(f"{Fore.CYAN}  Current state: Privacy OFF, enabling...")
                await self.enable_privacy()
                print(f"{Fore.YELLOW}🔘 Button pressed - Privacy ENABLED")
        
        except Exception as e:
            print(f"{Fore.RED}✗ Button press error: {e}")
            import traceback
            traceback.print_exc()
    
    async def enable_privacy(self):
        """Enable privacy mode for the camera."""
        try:
            camera = self.manager.get_camera_by_name(self.camera_name)
            if not camera:
                print(f"{Fore.RED}✗ Camera '{self.camera_name}' not found")
                return False
            
            # Enable privacy
            success = await self.manager.set_privacy_mode(camera, True)
            
            if success:
                self.privacy_enabled = True
                self.privacy_start_time = datetime.now()
                self.update_led()
                self.save_state()
                
                print(f"{Fore.YELLOW}🔒 Privacy enabled for {self.camera_name}")
                print(f"  Auto-disable in {self.timeout_minutes} minutes")
                
                return True
        
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to enable privacy: {e}")
            return False
    
    async def disable_privacy(self):
        """Disable privacy mode for the camera."""
        try:
            camera = self.manager.get_camera_by_name(self.camera_name)
            if not camera:
                print(f"{Fore.RED}✗ Camera '{self.camera_name}' not found")
                return False
            
            # Disable privacy
            success = await self.manager.set_privacy_mode(camera, False)
            
            if success:
                self.privacy_enabled = False
                self.privacy_start_time = None
                self.update_led()
                self.save_state()
                
                print(f"{Fore.GREEN}🔓 Privacy disabled for {self.camera_name}")
                
                return True
        
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to disable privacy: {e}")
            return False
    
    def update_led(self):
        """Update LED status based on privacy state."""
        if not self.led_pin:
            return
        
        if self.privacy_enabled:
            # Privacy on - LED off (or blinking)
            GPIO.output(self.led_pin, GPIO.LOW)
        else:
            # Privacy off - LED on
            GPIO.output(self.led_pin, GPIO.HIGH)
    
    async def check_timeout(self):
        """Check if privacy should be auto-disabled due to timeout."""
        if not self.privacy_enabled or not self.privacy_start_time:
            return
        
        elapsed = datetime.now() - self.privacy_start_time
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        
        if elapsed >= timeout_delta:
            print(f"{Fore.CYAN}⏰ Privacy timeout reached ({self.timeout_minutes} minutes)")
            await self.disable_privacy()
    
    def save_state(self):
        """Save current state to file for persistence."""
        state = {
            'privacy_enabled': self.privacy_enabled,
            'privacy_start_time': self.privacy_start_time.isoformat() if self.privacy_start_time else None,
            'camera_name': self.camera_name
        }
        
        try:
            # Create directory if it doesn't exist
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Failed to save state: {e}")
    
    def load_state(self):
        """Load previous state from file."""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.privacy_enabled = state.get('privacy_enabled', False)
            
            if state.get('privacy_start_time'):
                self.privacy_start_time = datetime.fromisoformat(state['privacy_start_time'])
            
            print(f"{Fore.CYAN}📄 Loaded previous state:")
            print(f"  Privacy: {'ENABLED' if self.privacy_enabled else 'DISABLED'}")
            
            if self.privacy_enabled and self.privacy_start_time:
                elapsed = datetime.now() - self.privacy_start_time
                remaining = timedelta(minutes=self.timeout_minutes) - elapsed
                
                if remaining.total_seconds() <= 0:
                    print(f"  Status: Timeout expired, will disable privacy")
                else:
                    mins = int(remaining.total_seconds() / 60)
                    print(f"  Auto-disable in: {mins} minutes")
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Failed to load state: {e}")
    
    async def connect_unifi(self):
        """Connect to UniFi Protect."""
        config = load_config()
        
        self.manager = UniFiProtectManager(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            verify_ssl=config['verify_ssl']
        )
        
        success = await self.manager.connect()
        if not success:
            return False
        
        # Verify camera exists
        camera = self.manager.get_camera_by_name(self.camera_name)
        if not camera:
            print(f"{Fore.RED}✗ Camera '{self.camera_name}' not found!")
            print(f"{Fore.CYAN}Available cameras:")
            for cam_id, cam_name, _ in self.manager.list_cameras():
                print(f"  - {cam_name}")
            return False
        
        print(f"{Fore.GREEN}✓ Found camera: {camera.name}")
        return True
    
    def cleanup(self):
        """Clean up GPIO and save state."""
        print(f"\n{Fore.CYAN}Cleaning up...")
        
        if self.led_pin:
            GPIO.output(self.led_pin, GPIO.LOW)
        
        GPIO.cleanup()
        self.save_state()
        
        print(f"{Fore.GREEN}✓ Cleanup complete")
    
    async def run(self):
        """Main controller loop - primarily for standalone use."""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}Starting Privacy Button Controller")
        print("=" * 40)
        
        # Load previous state
        self.load_state()
        
        # Small delay on startup (helps with service startup timing)
        print(f"{Fore.CYAN}Waiting for system startup...")
        await asyncio.sleep(5)
        
                # Connect to UniFi Protect (only if manager not already set by parent)
        if not self.manager:
            if not await self.connect_unifi():
                return False
        
        # Set up GPIO
        self.setup_gpio()
        
        # Update LED based on current state
        self.update_led()
        
        print(f"\n{Fore.GREEN}🚀 Privacy Button Controller is running!")
        print(f"{Fore.CYAN}Press the button to toggle privacy for '{self.camera_name}'")
        print(f"{Fore.CYAN}Press Ctrl+C to stop")
        
        try:
            # Main loop
            last_button_state = GPIO.input(self.button_pin)
            button_press_time = 0
            
            while self.running:
                # Check timeout
                await self.check_timeout()
                
                # Also poll button state as backup (in case interrupt fails)
                current_button_state = GPIO.input(self.button_pin)
                
                # Detect button press (HIGH to LOW transition)
                if last_button_state == GPIO.HIGH and current_button_state == GPIO.LOW:
                    current_time = time.time()
                    if current_time - button_press_time > 0.5:  # 500ms debounce
                        button_press_time = current_time
                        print(f"{Fore.MAGENTA}🔘 Button detected via polling backup")
                        await self.handle_button_press()
                
                last_button_state = current_button_state
                await asyncio.sleep(0.1)  # Check every 100ms
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Received stop signal")
        
        finally:
            self.cleanup()
        
        return True


class MultiCameraPrivacyController:
    """Controller for multiple cameras with individual GPIO buttons."""
    
    def __init__(self, config: Dict):
        """Initialize multi-camera controller."""
        self.config = config
        self.controllers: List[PrivacyButtonController] = []
        self.manager: Optional[UniFiProtectManager] = None
        self.global_settings = config.get('global_settings', {})
        self.running = True
        
        print(f"{Fore.CYAN}{Style.BRIGHT}Multi-Camera Privacy Controller")
        print("=" * 50)
    
    async def setup(self):
        """Set up all camera controllers."""
        # Connect to UniFi Protect once for all controllers
        print(f"{Fore.CYAN}Connecting to UniFi Protect...")
        unifi_config = load_config()
        
        self.manager = UniFiProtectManager(
            host=unifi_config['host'],
            port=unifi_config['port'],
            username=unifi_config['username'],
            password=unifi_config['password'],
            verify_ssl=unifi_config['verify_ssl']
        )
        
        success = await self.manager.connect()
        if not success:
            print(f"{Fore.RED}✗ Failed to connect to UniFi Protect")
            return False
        
        print(f"{Fore.GREEN}✓ Connected to UniFi Protect")
        
        # Create controllers for enabled cameras
        enabled_cameras = [cam for cam in self.config['cameras'] if cam.get('enabled', True)]
        
        for camera_config in enabled_cameras:
            try:
                # Verify camera exists
                camera = self.manager.get_camera_by_name(camera_config['name'])
                if not camera:
                    print(f"{Fore.YELLOW}⚠ Camera '{camera_config['name']}' not found, skipping")
                    continue
                
                # Create controller
                controller = PrivacyButtonController(
                    camera_name=camera_config['name'],
                    button_pin=camera_config['gpio_pin'],
                    led_pin=camera_config.get('led_pin'),
                    timeout_minutes=camera_config.get('timeout_minutes', 60)
                )
                
                # Share the UniFi manager
                controller.manager = self.manager
                
                # Set custom debounce time if specified
                if 'debounce_time' in self.global_settings:
                    controller.debounce_time = self.global_settings['debounce_time']
                
                # Set custom state file path if specified
                if 'state_file_path' in self.global_settings:
                    base_path = Path(self.global_settings['state_file_path'])
                    controller.state_file = base_path.parent / f"privacy_state_{camera_config['name']}.json"
                
                self.controllers.append(controller)
                print(f"{Fore.GREEN}✓ Added controller for '{camera_config['name']}' on GPIO {camera_config['gpio_pin']}")
                
            except Exception as e:
                print(f"{Fore.RED}✗ Failed to setup controller for '{camera_config['name']}': {e}")
        
        if not self.controllers:
            print(f"{Fore.RED}✗ No valid camera controllers created")
            return False
        
        # Set up GPIO for all controllers
        print(f"\n{Fore.CYAN}Setting up GPIO for {len(self.controllers)} cameras...")
        for controller in self.controllers:
            controller.setup_gpio()
            controller.load_state()
            controller.update_led()
        
        return True
    
    async def run(self):
        """Run the multi-camera controller."""
        if not await self.setup():
            return False
        
        startup_delay = self.global_settings.get('startup_delay', 5)
        print(f"{Fore.CYAN}Waiting {startup_delay}s for system startup...")
        await asyncio.sleep(startup_delay)
        
        print(f"\n{Fore.GREEN}🚀 Multi-Camera Privacy Controller is running!")
        print(f"{Fore.CYAN}Managing {len(self.controllers)} cameras:")
        for controller in self.controllers:
            status = "ENABLED" if controller.privacy_enabled else "DISABLED"
            print(f"  - {controller.camera_name}: GPIO {controller.button_pin} (Privacy: {status})")
        print(f"{Fore.CYAN}Press Ctrl+C to stop")
        
        try:
            polling_interval = self.global_settings.get('polling_interval', 0.1)
            
            # Initialize button state tracking for each controller
            button_states = {}
            button_press_times = {}
            
            for controller in self.controllers:
                button_states[controller.camera_name] = GPIO.input(controller.button_pin)
                button_press_times[controller.camera_name] = 0
            
            while self.running:
                # Check timeouts for all controllers
                timeout_tasks = [controller.check_timeout() for controller in self.controllers]
                await asyncio.gather(*timeout_tasks, return_exceptions=True)
                
                # Poll button states for all controllers (backup for failed interrupts)
                for controller in self.controllers:
                    try:
                        current_button_state = GPIO.input(controller.button_pin)
                        last_button_state = button_states[controller.camera_name]
                        
                        # Detect button press (HIGH to LOW transition)
                        if last_button_state == GPIO.HIGH and current_button_state == GPIO.LOW:
                            current_time = time.time()
                            if current_time - button_press_times[controller.camera_name] > 0.5:  # 500ms debounce
                                button_press_times[controller.camera_name] = current_time
                                print(f"{Fore.MAGENTA}🔘 Button detected via polling for {controller.camera_name}")
                                await controller.handle_button_press()
                        
                        button_states[controller.camera_name] = current_button_state
                        
                    except Exception as e:
                        print(f"{Fore.RED}✗ Button polling error for {controller.camera_name}: {e}")
                
                await asyncio.sleep(polling_interval)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Received stop signal")
        
        finally:
            self.cleanup()
        
        return True
    
    def cleanup(self):
        """Clean up all controllers."""
        print(f"\n{Fore.CYAN}Cleaning up multi-camera controller...")
        
        for controller in self.controllers:
            try:
                controller.cleanup()
            except Exception as e:
                print(f"{Fore.YELLOW}⚠ Cleanup error for {controller.camera_name}: {e}")
        
        print(f"{Fore.GREEN}✓ Multi-camera cleanup complete")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n{Fore.YELLOW}Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main function."""
    # Clean up any existing GPIO state first
    GPIO.setwarnings(False)
    GPIO.cleanup()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load camera configuration
    config = load_cameras_config()
    
    # Create and run multi-camera controller
    controller = MultiCameraPrivacyController(config)
    success = await controller.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        sys.exit(1) 