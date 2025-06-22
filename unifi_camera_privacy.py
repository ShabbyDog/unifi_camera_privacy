#!/usr/bin/env python3
"""
UniFi Protect Camera Privacy Zone Manager

This application allows you to toggle privacy zones for UniFi Protect cameras.
It provides both CLI and interactive modes for managing camera privacy settings.
"""

import asyncio
import os
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import click
from colorama import init, Fore, Style
from dotenv import load_dotenv
from uiprotect import ProtectApiClient
from uiprotect.data import Camera


# Initialize colorama for cross-platform colored output
init(autoreset=True)


class UniFiProtectManager:
    """Main class for managing UniFi Protect camera privacy zones."""
    
    def __init__(self, host: str, port: int, username: str, password: str, verify_ssl: bool = True):
        """Initialize the UniFi Protect manager."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.client: Optional[ProtectApiClient] = None
        self.cameras: Dict[str, Camera] = {}
    
    async def connect(self) -> bool:
        """Connect to UniFi Protect and initialize the client."""
        try:
            self.client = ProtectApiClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                verify_ssl=self.verify_ssl
            )
            
            # Initialize the client and get bootstrap data
            await self.client.update()
            self.cameras = self.client.bootstrap.cameras
            
            print(f"{Fore.GREEN}✓ Successfully connected to UniFi Protect at {self.host}")
            print(f"{Fore.CYAN}Found {len(self.cameras)} camera(s)")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to connect to UniFi Protect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from UniFi Protect."""
        if self.client:
            # The client doesn't have an explicit disconnect method in the current version
            # but the websocket connection will be closed when the object is destroyed
            pass
    
    def list_cameras(self) -> List[Tuple[str, str, bool]]:
        """Get a list of all cameras with their privacy zone status."""
        camera_list = []
        for camera_id, camera in self.cameras.items():
            # Check if camera has any privacy zones
            has_privacy_zone = len(camera.privacy_zones) > 0
            camera_list.append((camera_id, camera.name, has_privacy_zone))
        
        return camera_list
    
    def get_camera_by_name(self, name: str) -> Optional[Camera]:
        """Get a camera by its name."""
        for camera in self.cameras.values():
            if camera.name.lower() == name.lower():
                return camera
        return None
    
    def get_camera_by_id(self, camera_id: str) -> Optional[Camera]:
        """Get a camera by its ID."""
        return self.cameras.get(camera_id)
    
    async def toggle_privacy_zone(self, camera: Camera) -> bool:
        """Toggle privacy zone for a camera."""
        try:
            if len(camera.privacy_zones) > 0:
                # Camera has privacy zones - remove them (enable camera)
                await self.remove_privacy_zones(camera)
                await self.set_led_normal(camera)
                await self.set_ir_led_auto(camera)
                print(f"{Fore.GREEN}✓ Privacy zone disabled for camera '{camera.name}'")
                return True
            else:
                # Camera has no privacy zones - add one (disable camera)
                await self.add_privacy_zone(camera)
                await self.set_led_privacy_mode(camera)
                await self.set_ir_led_off(camera)
                print(f"{Fore.YELLOW}✓ Privacy zone enabled for camera '{camera.name}'")
                return True
                
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to toggle privacy zone for camera '{camera.name}': {e}")
            return False
    
    async def add_privacy_zone(self, camera: Camera):
        """Add a privacy zone that covers the entire camera view."""
        # Create a privacy zone that covers the entire frame
        # Coordinates are normalized (0.0 to 1.0)
        privacy_zone_points = [
            [0.0, 0.0],  # Top-left
            [1.0, 0.0],  # Top-right
            [1.0, 1.0],  # Bottom-right
            [0.0, 1.0]   # Bottom-left
        ]
        
        # Use the uiprotect library's method to create privacy zone
        try:
            await camera.create_privacy_zone(points=privacy_zone_points)
        except AttributeError:
            # Fallback for different uiprotect library versions
            # Try using the set_privacy method instead
            await camera.set_privacy(True, 0)
    
    async def remove_privacy_zones(self, camera: Camera):
        """Remove all privacy zones from a camera."""
        try:
            # Remove all existing privacy zones
            for privacy_zone in camera.privacy_zones:
                await privacy_zone.delete()
        except (AttributeError, TypeError):
            # Fallback for different uiprotect library versions
            # Try using the set_privacy method instead
            await camera.set_privacy(False)
    
    async def set_privacy_mode(self, camera: Camera, enabled: bool) -> bool:
        """Set privacy mode for a camera (alternative method)."""
        try:
            if enabled:
                # Enable privacy mode (this typically disables recording and creates a privacy zone)
                await camera.set_privacy(True, 0)  # 0 = mic level when in privacy mode
                await self.set_led_privacy_mode(camera)
                await self.set_ir_led_off(camera)
            else:
                # Disable privacy mode
                await camera.set_privacy(False)
                await self.set_led_normal(camera)
                await self.set_ir_led_auto(camera)
            
            action = "enabled" if enabled else "disabled"
            print(f"{Fore.GREEN}✓ Privacy mode {action} for camera '{camera.name}'")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to set privacy mode for camera '{camera.name}': {e}")
            return False
    
    async def set_led_privacy_mode(self, camera: Camera):
        """Set LED to indicate privacy mode (blink or turn off)."""
        try:
            # Method 1: Try to turn off the status light completely
            if hasattr(camera, 'set_status_light'):
                await camera.set_status_light(False)
                print(f"{Fore.CYAN}  └─ LED turned OFF for privacy")
                return
            
            # Method 2: Try setting LED settings via camera settings
            if hasattr(camera, 'update_device'):
                # Try updating LED settings - different cameras may have different property names
                led_settings = {
                    'status_light': False,  # Turn off status light
                    'led_enabled': False,   # Alternative property name
                    'indicator_light': False  # Another alternative
                }
                
                for setting_name, value in led_settings.items():
                    try:
                        await camera.update_device({setting_name: value})
                        print(f"{Fore.CYAN}  └─ LED turned OFF via {setting_name}")
                        return
                    except:
                        continue
            
            # Method 3: Try blinking mode if available
            if hasattr(camera, 'set_led_mode'):
                try:
                    await camera.set_led_mode('blink')  # or 'flash'
                    print(f"{Fore.CYAN}  └─ LED set to BLINK for privacy")
                    return
                except:
                    pass
            
            print(f"{Fore.YELLOW}  └─ LED control not available for this camera model")
            
        except Exception as e:
            print(f"{Fore.YELLOW}  └─ LED control failed: {e}")
    
    async def set_led_normal(self, camera: Camera):
        """Set LED back to normal operation."""
        try:
            # Method 1: Try to turn on the status light
            if hasattr(camera, 'set_status_light'):
                await camera.set_status_light(True)
                print(f"{Fore.CYAN}  └─ LED restored to normal")
                return
            
            # Method 2: Try setting LED settings via camera settings
            if hasattr(camera, 'update_device'):
                # Try updating LED settings
                led_settings = {
                    'status_light': True,   # Turn on status light
                    'led_enabled': True,    # Alternative property name
                    'indicator_light': True # Another alternative
                }
                
                for setting_name, value in led_settings.items():
                    try:
                        await camera.update_device({setting_name: value})
                        print(f"{Fore.CYAN}  └─ LED restored via {setting_name}")
                        return
                    except:
                        continue
            
            # Method 3: Try normal/solid mode if available
            if hasattr(camera, 'set_led_mode'):
                try:
                    await camera.set_led_mode('normal')  # or 'solid'
                    print(f"{Fore.CYAN}  └─ LED set to normal mode")
                    return
                except:
                    pass
            
            print(f"{Fore.YELLOW}  └─ LED control not available for this camera model")
            
        except Exception as e:
            print(f"{Fore.YELLOW}  └─ LED control failed: {e}")

    async def set_ir_led_off(self, camera: Camera):
        """Turn off IR LEDs for enhanced privacy."""
        try:
            from uiprotect.data.types import IRLEDMode
            
            if hasattr(camera, 'set_ir_led_model') and camera.feature_flags.has_led_ir:
                await camera.set_ir_led_model(IRLEDMode.OFF)
                print(f"{Fore.CYAN}  └─ IR LEDs turned OFF for enhanced privacy")
                return True
            else:
                print(f"{Fore.YELLOW}  └─ IR LED control not available for this camera model")
                return False
                
        except Exception as e:
            print(f"{Fore.YELLOW}  └─ IR LED control failed: {e}")
            return False

    async def set_ir_led_auto(self, camera: Camera):
        """Restore IR LEDs to automatic mode."""
        try:
            from uiprotect.data.types import IRLEDMode
            
            if hasattr(camera, 'set_ir_led_model') and camera.feature_flags.has_led_ir:
                await camera.set_ir_led_model(IRLEDMode.AUTO)
                print(f"{Fore.CYAN}  └─ IR LEDs restored to AUTO mode")
                return True
            else:
                print(f"{Fore.YELLOW}  └─ IR LED control not available for this camera model")
                return False
                
        except Exception as e:
            print(f"{Fore.YELLOW}  └─ IR LED control failed: {e}")
            return False

    async def get_ir_led_status(self, camera: Camera) -> str:
        """Get current IR LED status."""
        try:
            if hasattr(camera, 'isp_settings') and camera.feature_flags.has_led_ir:
                ir_mode = camera.isp_settings.ir_led_mode
                return str(ir_mode).upper()
            else:
                return "NOT_AVAILABLE"
                
        except Exception:
            return "UNKNOWN"
    
    async def get_led_status(self, camera: Camera) -> str:
        """Get current LED status."""
        try:
            # Check various possible LED status properties
            led_properties = ['status_light', 'led_enabled', 'indicator_light']
            
            for prop in led_properties:
                if hasattr(camera, prop):
                    status = getattr(camera, prop)
                    if status is not None:
                        return "ON" if status else "OFF"
            
            return "UNKNOWN"
            
        except Exception:
            return "UNKNOWN"


def load_config() -> Dict[str, str]:
    """Load configuration from environment variables."""
    # Try to load from .env file first
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
    
    config = {
        'host': os.getenv('UFP_HOST', ''),
        'port': int(os.getenv('UFP_PORT', '443')),
        'username': os.getenv('UFP_USERNAME', ''),
        'password': os.getenv('UFP_PASSWORD', ''),
        'verify_ssl': os.getenv('UFP_SSL_VERIFY', 'True').lower() == 'true'
    }
    
    return config


def validate_config(config: Dict) -> List[str]:
    """Validate the configuration and return list of missing parameters."""
    missing = []
    required_fields = ['host', 'username', 'password']
    
    for field in required_fields:
        if not config.get(field):
            missing.append(field.upper())
    
    return missing


async def interactive_mode():
    """Run the application in interactive mode."""
    print(f"{Fore.CYAN}{Style.BRIGHT}UniFi Protect Camera Privacy Manager")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    missing = validate_config(config)
    
    if missing:
        print(f"{Fore.RED}Missing required configuration:")
        for field in missing:
            print(f"  - {field}")
        print(f"\nPlease set these environment variables or create a .env file.")
        print(f"See config.env.example for reference.")
        return False
    
    # Connect to UniFi Protect
    manager = UniFiProtectManager(
        host=config['host'],
        port=config['port'],
        username=config['username'],
        password=config['password'],
        verify_ssl=config['verify_ssl']
    )
    
    if not await manager.connect():
        return False
    
    try:
        while True:
            print(f"\n{Fore.CYAN}Available cameras:")
            cameras = manager.list_cameras()
            
            if not cameras:
                print(f"{Fore.YELLOW}No cameras found.")
                break
            
            for i, (camera_id, name, has_privacy) in enumerate(cameras, 1):
                camera_obj = manager.get_camera_by_id(camera_id)
                privacy_status = f"{Fore.RED}[PRIVACY ON]" if has_privacy else f"{Fore.GREEN}[PRIVACY OFF]"
                led_status = await manager.get_led_status(camera_obj) if camera_obj else "UNKNOWN"
                led_color = Fore.RED if led_status == "OFF" else Fore.GREEN if led_status == "ON" else Fore.YELLOW
                print(f"  {i}. {name} {privacy_status} {led_color}[LED {led_status}]")
            
            print(f"\n{Fore.CYAN}Options:")
            print("  Enter camera number to toggle privacy zone")
            print("  'q' to quit")
            
            choice = input(f"\n{Fore.WHITE}Your choice: ").strip()
            
            if choice.lower() == 'q':
                break
            
            try:
                camera_num = int(choice)
                if 1 <= camera_num <= len(cameras):
                    camera_id, camera_name, _ = cameras[camera_num - 1]
                    camera = manager.get_camera_by_id(camera_id)
                    if camera:
                        await manager.toggle_privacy_zone(camera)
                    else:
                        print(f"{Fore.RED}✗ Camera not found")
                else:
                    print(f"{Fore.RED}✗ Invalid camera number")
            except ValueError:
                print(f"{Fore.RED}✗ Invalid input")
    
    finally:
        await manager.disconnect()
    
    return True


@click.command()
@click.option('--host', '-h', help='UniFi Protect host address')
@click.option('--port', '-p', default=443, help='UniFi Protect port')
@click.option('--username', '-u', help='UniFi Protect username')
@click.option('--password', '-w', help='UniFi Protect password')
@click.option('--no-ssl-verify', is_flag=True, help='Disable SSL verification')
@click.option('--camera', '-c', help='Camera name or ID to toggle')
@click.option('--list', 'list_cameras', is_flag=True, help='List all cameras')
@click.option('--enable-privacy', is_flag=True, help='Enable privacy mode for specified camera')
@click.option('--disable-privacy', is_flag=True, help='Disable privacy mode for specified camera')
@click.option('--led-off', is_flag=True, help='Turn off LED for specified camera')
@click.option('--led-on', is_flag=True, help='Turn on LED for specified camera')
@click.option('--led-status', is_flag=True, help='Show LED status for specified camera')
@click.option('--ir-off', is_flag=True, help='Turn off IR LEDs for specified camera')
@click.option('--ir-auto', is_flag=True, help='Set IR LEDs to auto mode for specified camera')
@click.option('--ir-status', is_flag=True, help='Show IR LED status for specified camera')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
def main(host, port, username, password, no_ssl_verify, camera, list_cameras, 
         enable_privacy, disable_privacy, led_off, led_on, led_status, 
         ir_off, ir_auto, ir_status, interactive):
    """UniFi Protect Camera Privacy Zone Manager
    
    Toggle privacy zones and control LED status lights and IR LEDs for UniFi Protect cameras.
    Supports both command line and interactive modes for camera management.
    Configuration can be provided via command line arguments or environment variables.
    
    Privacy Features:
    - Privacy zones: Block camera view with full-screen privacy zone
    - Status LED control: Turn LED off when privacy enabled (visual indicator)
    - IR LED control: Turn off IR LEDs when privacy enabled (enhanced privacy)
    - Automatic restoration: LED and IR LEDs restored when privacy disabled
    
    Manual Control:
    - Independent LED control (on/off/status)
    - Independent IR LED control (off/auto/status)
    - Perfect for automation and smart home integration
    """
    
    async def run_app():
        # Load config from environment if not provided via CLI
        env_config = load_config()
        
        # Override with CLI arguments if provided
        config = {
            'host': host or env_config['host'],
            'port': port,
            'username': username or env_config['username'],
            'password': password or env_config['password'],
            'verify_ssl': not no_ssl_verify and env_config['verify_ssl']
        }
        
        # If interactive mode or no specific action, run interactive
        if interactive or (not list_cameras and not camera):
            return await interactive_mode()
        
        # Validate configuration
        missing = validate_config(config)
        if missing:
            print(f"{Fore.RED}Missing required configuration:")
            for field in missing:
                print(f"  - {field}")
            return False
        
        # Connect to UniFi Protect
        manager = UniFiProtectManager(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            verify_ssl=config['verify_ssl']
        )
        
        if not await manager.connect():
            return False
        
        try:
            if list_cameras:
                # List all cameras
                cameras = manager.list_cameras()
                if cameras:
                    print(f"\n{Fore.CYAN}Available cameras:")
                    for camera_id, name, has_privacy in cameras:
                        status = f"{Fore.RED}[PRIVACY ON]" if has_privacy else f"{Fore.GREEN}[PRIVACY OFF]"
                        print(f"  {camera_id}: {name} {status}")
                else:
                    print(f"{Fore.YELLOW}No cameras found.")
                
                return True
            
            if camera:
                # Find camera by name or ID
                cam_obj = manager.get_camera_by_name(camera) or manager.get_camera_by_id(camera)
                if not cam_obj:
                    print(f"{Fore.RED}✗ Camera '{camera}' not found")
                    return False
                
                # Check for conflicting options
                privacy_options = [enable_privacy, disable_privacy]
                led_options = [led_off, led_on, led_status]
                ir_options = [ir_off, ir_auto, ir_status]
                
                if sum(privacy_options) > 1:
                    print(f"{Fore.RED}✗ Cannot specify multiple privacy options")
                    return False
                
                if sum(led_options) > 1:
                    print(f"{Fore.RED}✗ Cannot specify multiple LED options")
                    return False
                
                if sum(ir_options) > 1:
                    print(f"{Fore.RED}✗ Cannot specify multiple IR LED options")
                    return False
                
                # Handle LED control
                if led_off:
                    await manager.set_led_privacy_mode(cam_obj)
                    return True
                elif led_on:
                    await manager.set_led_normal(cam_obj)
                    return True
                elif led_status:
                    status = await manager.get_led_status(cam_obj)
                    color = Fore.RED if status == "OFF" else Fore.GREEN if status == "ON" else Fore.YELLOW
                    print(f"{color}LED Status for '{cam_obj.name}': {status}")
                    return True
                
                # Handle IR LED control
                if ir_off:
                    await manager.set_ir_led_off(cam_obj)
                    return True
                elif ir_auto:
                    await manager.set_ir_led_auto(cam_obj)
                    return True
                elif ir_status:
                    status = await manager.get_ir_led_status(cam_obj)
                    if status == "NOT_AVAILABLE":
                        color = Fore.YELLOW
                    elif status == "OFF":
                        color = Fore.RED
                    elif status in ["AUTO", "ON"]:
                        color = Fore.GREEN
                    else:
                        color = Fore.YELLOW
                    print(f"{color}IR LED Status for '{cam_obj.name}': {status}")
                    return True
                
                # Handle privacy control
                if enable_privacy:
                    return await manager.set_privacy_mode(cam_obj, True)
                elif disable_privacy:
                    return await manager.set_privacy_mode(cam_obj, False)
                else:
                    # Toggle privacy zone
                    return await manager.toggle_privacy_zone(cam_obj)
        
        finally:
            await manager.disconnect()
        
        return True
    
    # Run the async application
    success = asyncio.run(run_app())
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 