import ppadb.client
import ppadb.device
import subprocess
import time
import cv2
import pathlib
from Constants import Emulators
from typing import Optional

Emulator_Path: str | None = None


def time_function(func, *args, **kwargs) -> any:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    delta = end - start
    # make it to a h m s format or m s format or s format depending on the time
    if delta > 3600:
        delta = f"{delta // 3600}h {delta % 3600 // 60}m {delta % 60:.2f}s"
    elif delta > 60:
        delta = f"{delta // 60}m {delta % 60:.2f}s"
    else:
        delta = f"{delta:.2f}s"
    print(f"Time taken for {func.__name__} is {delta}, result is {result}")
    return result


def close_emulator():
    if Emulator_Path is not None:
        emulator_name = Emulator_Path.split("\\")[-1]
        try:
            # subprocess.call(["taskkill", "/IM", emulator_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
            subprocess.call(["taskkill", "/F", "/IM", emulator_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
            print("Emulator closed")
            return True
        except Exception as e:
            print(e)
            return False


def open_emulator():
    close_emulator()
    time.sleep(2)
    if Emulator_Path is not None:
        subprocess.Popen(Emulator_Path, creationflags=subprocess.CREATE_NEW_CONSOLE)
    time.sleep(15)


def connect_to_any_device(port: int = None) -> Optional[ppadb.device.Device]:
    subprocess.Popen(r"platform-tools\adb.exe kill-server", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(2.5)

    subprocess.Popen(r"platform-tools\adb.exe start-server", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    time.sleep(2.5)
    if port is None:
        client = ppadb.client.Client()
    else:
        client = ppadb.client.Client(port=port)
    devices = client.devices()
    if len(devices) == 0:
        print('No devices attached')
    else:
        for device in devices:
            if device:
                try:
                    if device.shell('wm size').count("1280x720") > 0:
                        return device
                    else:
                        print(f'Device screen size is not 1280x720, its: {device.shell("wm size")}')
                        # print(device.shell('wm density'))
                        # print the dpi of the device
                        device.shell('wm density 240')
                        # print(device.shell('wm density reset'))
                        # print(device.shell('wm density'))
                        return device
                except Exception as e:
                    print('Device is not responding', e)
    subprocess.Popen(r"platform-tools\adb.exe kill-server", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return None


def compare_imgs(img1, img2, transform_to_black=False):
    if img1.shape == img2.shape:
        height, width, _ = img2.shape
        if transform_to_black:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        errorL2 = cv2.norm(img1, img2, cv2.NORM_L2)
        similarity = 1 - errorL2 / (height * width)
        return similarity > 0.99
    return False


for emulator_path in Emulators.values():
    if pathlib.Path(emulator_path).exists():
        Emulator_Path = emulator_path
        break
else:
    raise Exception("No emulator found")
