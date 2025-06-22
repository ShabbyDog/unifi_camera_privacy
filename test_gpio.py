#!/usr/bin/env python3
"""
Simple GPIO button test script

This tests if the button hardware and GPIO setup is working correctly.
"""

import time
import sys

try:
    import RPi.GPIO as GPIO
except ImportError:
    print("ERROR: RPi.GPIO not installed!")
    print("Install with: pip install RPi.GPIO")
    sys.exit(1)

# Configuration
BUTTON_PIN = 18
LED_PIN = 24

def test_gpio():
    """Test GPIO functionality."""
    print("=== GPIO Button Test ===")
    print(f"Button Pin: GPIO {BUTTON_PIN}")
    print(f"LED Pin: GPIO {LED_PIN}")
    print()
    
    try:
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(LED_PIN, GPIO.OUT)
        
        print("✓ GPIO setup successful")
        
        # Test LED
        print("Testing LED...")
        for i in range(3):
            GPIO.output(LED_PIN, GPIO.HIGH)
            print("  LED ON")
            time.sleep(0.5)
            GPIO.output(LED_PIN, GPIO.LOW)
            print("  LED OFF")
            time.sleep(0.5)
        
        print("\n✓ LED test complete")
        
        # Test button
        print(f"\nTesting button on GPIO {BUTTON_PIN}...")
        print("Press the button (Ctrl+C to exit)")
        
        button_pressed = False
        last_state = GPIO.input(BUTTON_PIN)
        
        while True:
            current_state = GPIO.input(BUTTON_PIN)
            
            # Button pressed (goes from HIGH to LOW with pull-up)
            if last_state == GPIO.HIGH and current_state == GPIO.LOW:
                print("🔘 BUTTON PRESSED!")
                button_pressed = True
                
                # Flash LED on button press
                GPIO.output(LED_PIN, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(LED_PIN, GPIO.LOW)
            
            last_state = current_state
            time.sleep(0.01)  # Small delay
        
    except KeyboardInterrupt:
        print(f"\n\nTest interrupted")
        if button_pressed:
            print("✓ Button is working correctly!")
        else:
            print("✗ Button was not detected")
            print("\nTroubleshooting:")
            print("1. Check button wiring:")
            print(f"   - One side to GPIO {BUTTON_PIN} (Physical pin 12)")
            print("   - Other side to GND (Physical pin 14)")
            print("2. Ensure button is 'normally open' type")
            print("3. Check connections are secure")
        
    except Exception as e:
        print(f"❌ GPIO Error: {e}")
        print("\nPossible causes:")
        print("1. Permission issue - try: sudo usermod -a -G gpio $USER")
        print("2. Need to reboot after adding to gpio group")
        print("3. Hardware not connected properly")
        
    finally:
        GPIO.cleanup()
        print("🧹 GPIO cleanup complete")

if __name__ == "__main__":
    test_gpio() 