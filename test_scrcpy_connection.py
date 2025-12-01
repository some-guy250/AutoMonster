"""Test script to diagnose scrcpy connection issues"""
import time
import sys
from adbutils import adb
from scrcpy import Client as scrcpy_Client

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import os
    os.system('chcp 65001 >nul 2>&1')

def test_connection():
    print("=== Scrcpy Connection Test ===")

    # Check for devices
    print("\n1. Checking for ADB devices...")
    devices = adb.device_list()
    if not devices:
        print("ERROR: No ADB devices found!")
        print("Please ensure:")
        print("  - Device is connected via USB or network")
        print("  - USB debugging is enabled")
        print("  - Device is authorized (check device screen for prompt)")
        return False

    device = devices[0]
    print(f"[OK] Found device: {device.serial}")

    # Check device properties
    print("\n2. Checking device properties...")
    try:
        android_version = device.shell('getprop ro.build.version.release').strip()
        print(f"[OK] Android version: {android_version}")

        # Check if screen is on
        screen_state = device.shell('dumpsys power | grep "Display Power"').strip()
        print(f"[OK] Screen state: {screen_state}")

    except Exception as e:
        print(f"WARNING: Could not get device properties: {e}")

    # Check for existing scrcpy processes
    print("\n3. Checking for existing scrcpy processes...")
    try:
        ps_output = device.shell('ps | grep scrcpy').strip()
        if ps_output:
            print(f"WARNING: Found existing scrcpy process:")
            print(ps_output)
            print("Attempting to kill existing process...")
            device.shell('pkill -9 app_process')
            time.sleep(1)
        else:
            print("[OK] No existing scrcpy processes found")
    except Exception as e:
        print(f"INFO: Could not check for scrcpy processes: {e}")

    # Try to connect with scrcpy
    print("\n4. Attempting to connect with scrcpy...")
    client = scrcpy_Client(max_fps=10, max_size=None, device=device)

    try:
        print("Starting scrcpy client (this may take a few seconds)...")
        client.start(threaded=True)
        print("[OK] Successfully connected to scrcpy-server!")

        # Wait a bit and check if we can get frames
        print("\n5. Testing frame capture...")
        time.sleep(2)
        frame = client.last_frame
        if frame is not None:
            print(f"[OK] Successfully captured frame: {frame.shape}")
        else:
            print("WARNING: Could not capture frame")

        print("\n6. Stopping client...")
        client.stop()
        print("[OK] Client stopped successfully")

        print("\n=== CONNECTION TEST PASSED ===")
        return True

    except ConnectionError as e:
        print(f"\n[FAILED] CONNECTION FAILED: {e}")
        print("\nTroubleshooting steps:")
        print("1. Unlock your device screen")
        print("2. Ensure USB debugging is enabled")
        print("3. Check if device is authorized (adb devices should show 'device', not 'unauthorized')")
        print("4. Try running: adb kill-server && adb start-server")
        print("5. Restart your device")
        print("6. Try a different USB cable/port")
        return False
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_connection()
