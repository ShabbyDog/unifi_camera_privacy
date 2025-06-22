#!/usr/bin/env python3
"""
UniFi Protect Connection Test Script

This script helps you test your connection to UniFi Protect before using the main application.
"""

import asyncio
import os
import sys
from pathlib import Path

from colorama import init, Fore, Style
from dotenv import load_dotenv

try:
    from uiprotect import ProtectApiClient
except ImportError:
    print(f"{Fore.RED}Error: uiprotect library not found. Please install dependencies with:")
    print(f"pip install -r requirements.txt")
    sys.exit(1)

# Initialize colorama
init(autoreset=True)


def load_config():
    """Load configuration from environment variables."""
    # Try to load from .env file first
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"{Fore.GREEN}✓ Found .env file")
    else:
        print(f"{Fore.YELLOW}⚠ No .env file found, using environment variables")
    
    config = {
        'host': os.getenv('UFP_HOST', ''),
        'port': int(os.getenv('UFP_PORT', '443')),
        'username': os.getenv('UFP_USERNAME', ''),
        'password': os.getenv('UFP_PASSWORD', ''),
        'verify_ssl': os.getenv('UFP_SSL_VERIFY', 'True').lower() == 'true'
    }
    
    return config


async def test_connection():
    """Test connection to UniFi Protect."""
    print(f"{Fore.CYAN}{Style.BRIGHT}UniFi Protect Connection Test")
    print("=" * 35)
    
    # Load configuration
    config = load_config()
    
    # Check required configuration
    missing = []
    required_fields = ['host', 'username', 'password']
    
    for field in required_fields:
        if not config.get(field):
            missing.append(field.upper())
    
    if missing:
        print(f"{Fore.RED}✗ Missing required configuration:")
        for field in missing:
            print(f"  - {field}")
        print(f"\nPlease set these environment variables or create a .env file.")
        print(f"See config.env.example for reference.")
        return False
    
    # Display configuration (without password)
    print(f"\n{Fore.CYAN}Configuration:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Username: {config['username']}")
    print(f"  Password: {'*' * len(config['password'])}")
    print(f"  SSL Verify: {config['verify_ssl']}")
    
    # Test connection
    print(f"\n{Fore.CYAN}Testing connection...")
    
    try:
        client = ProtectApiClient(
            host=config['host'],
            port=config['port'],
            username=config['username'],
            password=config['password'],
            verify_ssl=config['verify_ssl']
        )
        
        # Initialize the client
        await client.update()
        
        print(f"{Fore.GREEN}✓ Successfully connected to UniFi Protect!")
        
        # Get system information
        nvr = client.bootstrap.nvr
        print(f"\n{Fore.CYAN}System Information:")
        print(f"  NVR Name: {nvr.name}")
        print(f"  Version: {nvr.version}")
        print(f"  Host: {nvr.host}")
        # Handle different uiprotect library versions
        try:
            print(f"  Uptime: {nvr.uptime_pretty}")
        except AttributeError:
            if hasattr(nvr, 'uptime'):
                print(f"  Uptime: {nvr.uptime} seconds")
            else:
                print(f"  Uptime: Not available")
        
        # Get camera information
        cameras = client.bootstrap.cameras
        print(f"\n{Fore.CYAN}Cameras Found: {len(cameras)}")
        
        if cameras:
            for i, (camera_id, camera) in enumerate(cameras.items(), 1):
                privacy_status = "PRIVACY ON" if len(camera.privacy_zones) > 0 else "PRIVACY OFF"
                privacy_color = Fore.RED if len(camera.privacy_zones) > 0 else Fore.GREEN
                online_status = "ONLINE" if camera.is_connected else "OFFLINE"
                online_color = Fore.GREEN if camera.is_connected else Fore.RED
                
                print(f"  {i}. {camera.name}")
                print(f"     ID: {camera_id}")
                print(f"     Status: {online_color}{online_status}{Style.RESET_ALL}")
                print(f"     Privacy: {privacy_color}{privacy_status}{Style.RESET_ALL}")
                print(f"     Model: {camera.model}")
                print(f"     Firmware: {camera.firmware_version}")
                print()
        
        print(f"{Fore.GREEN}✓ Connection test completed successfully!")
        print(f"\n{Fore.CYAN}You can now use the main application:")
        print(f"  python unifi_camera_privacy.py --interactive")
        
        # Clean up the client session
        if hasattr(client, '_session') and client._session:
            await client._session.close()
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}✗ Connection failed: {e}")
        
        # Provide troubleshooting suggestions
        print(f"\n{Fore.YELLOW}Troubleshooting suggestions:")
        print(f"  1. Verify your host IP address is correct")
        print(f"  2. Check if UniFi Protect is running on the specified port")
        print(f"  3. Ensure your username and password are correct")
        print(f"  4. Make sure you're using a local user account (not SSO)")
        print(f"  5. If using self-signed certificates, try setting UFP_SSL_VERIFY=False")
        print(f"  6. Check if there's a firewall blocking the connection")
        
        return False


def main():
    """Main function."""
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 