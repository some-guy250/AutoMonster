import time
import logging
from adbutils import adb

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_unlock():
    try:
        devices = adb.device_list()
        if not devices:
            logger.error("No ADB devices found")
            return
        
        device = devices[0]
        logger.info(f"Connected to device: {device.serial}")

        # 1. Wake up the device
        logger.info("Checking power state...")
        dump_power = device.shell("dumpsys power")
        is_screen_on = "mWakefulness=Awake" in dump_power
        logger.info(f"Screen on: {is_screen_on}")
        
        if not is_screen_on:
            logger.info("Screen is off, turning it on...")
            device.shell("input keyevent KEYCODE_WAKEUP")
            time.sleep(1.0)
            # Recheck
            dump_power = device.shell("dumpsys power")
            is_screen_on = "mWakefulness=Awake" in dump_power
            logger.info(f"Screen on after wakeup: {is_screen_on}")
        
        # 2. Check if locked
        logger.info("Checking lock state...")
        dump_policy = device.shell("dumpsys window policy")
        # Check multiple possible indicators
        is_locked = ("mIsShowing=true" in dump_policy or 
                    "mKeyguardShowing=true" in dump_policy or
                    "showing=true" in dump_policy.lower())
        logger.info(f"Device locked: {is_locked}")
        
        # Debug: print relevant parts of dump_policy
        logger.info("Lock state details:")
        for line in dump_policy.splitlines():
            if "Keyguard" in line or "Showing" in line:
                logger.info(f"  {line.strip()}")
        
        if is_locked:
            logger.info("Device is locked. Attempting unlock methods...")
            
            # Method A: Menu Key (82)
            logger.info("Method A: KEYCODE_MENU (82)")
            device.shell("input keyevent 82")
            time.sleep(1.0)
            
            # Check if unlocked
            dump_policy = device.shell("dumpsys window policy")
            is_still_locked = ("mIsShowing=true" in dump_policy or "mKeyguardShowing=true" in dump_policy)
            if not is_still_locked:
                logger.info("Unlocked with Method A!")
                return

            # Method B: Direct Dismiss Command
            logger.info("Method B: wm dismiss-keyguard")
            device.shell("wm dismiss-keyguard")
            time.sleep(1.0)

            # Check if unlocked
            dump_policy = device.shell("dumpsys window policy")
            is_still_locked = ("mIsShowing=true" in dump_policy or "mKeyguardShowing=true" in dump_policy)
            if not is_still_locked:
                logger.info("Unlocked with Method B!")
                return
            
            # Method C: Swipe Up
            logger.info("Method C: Swipe Up")
            wm_size = device.shell("wm size")
            width, height = 1080, 1920 # Safe defaults
            if "Physical size:" in wm_size:
                try:
                    for line in wm_size.splitlines():
                        if "Physical size:" in line:
                            res_str = line.split("Physical size: ")[1].strip()
                            w, h = map(int, res_str.split("x"))
                            width, height = w, h
                            break
                except Exception:
                    logger.warning("Failed to parse resolution, using defaults")
            
            logger.info(f"Resolution: {width}x{height}")

            center_x = width // 2
            start_y = int(height * 0.85)
            end_y = int(height * 0.15)
            
            logger.info(f"Swiping from ({center_x}, {start_y}) to ({center_x}, {end_y}) duration 300ms")
            device.shell(f"input swipe {center_x} {start_y} {center_x} {end_y} 300")
            time.sleep(1.0)
            
            # Check if unlocked
            dump_policy = device.shell("dumpsys window policy")
            is_still_locked = ("mIsShowing=true" in dump_policy or "mKeyguardShowing=true" in dump_policy)
            if not is_still_locked:
                logger.info("Unlocked with Method C!")
                return

            # Method D: Longer Swipe
            logger.info("Method D: Longer Swipe (1000ms)")
            device.shell(f"input swipe {center_x} {int(height * 0.9)} {center_x} {int(height * 0.1)} 1000")
            time.sleep(1.0)

            # Final Check
            dump_policy = device.shell("dumpsys window policy")
            is_still_locked = ("mIsShowing=true" in dump_policy or "mKeyguardShowing=true" in dump_policy)
            if not is_still_locked:
                logger.info("Unlocked with Method D!")
            else:
                logger.error("Failed to unlock device with all methods.")
        else:
            logger.info("Device is already unlocked.")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    debug_unlock()