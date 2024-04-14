import os
from urllib.request import urlopen
from zipfile import ZipFile

import ppadb.client
import ppadb.device
import subprocess
import time
import cv2
import pathlib

import requests
from tqdm import tqdm

# from Constants import Emulators
from typing import Optional


# Emulator_Path: str | None = None


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
                        # print(f'Device screen size is not 1280x720, its: {size[0]}x{size[1]}')
                        # print(device.shell('wm density'))
                        # print the dpi of the device
                        # device.shell('wm density 240')
                        # # print(device.shell('wm density reset'))
                        # if device.shell('wm density').count("240") == 0:
                        #     raise Exception("Density cannot be set to 240")
                        return device
                except Exception as e:
                    print(e)
    subprocess.Popen(r"platform-tools\adb.exe kill-server", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return None


def get_size(device: ppadb.device.Device) -> tuple[int, ...]:
    size = device.shell('wm size')
    tuple_size = tuple(map(int, size.split("Physical size: ")[1].split("x")))
    return tuple_size

# def reset_density(device: ppadb.device.Device):
#     device.shell('wm density reset')


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


def check_platform_tools():
    if not (pathlib.Path("platform-tools").is_dir() and pathlib.Path("platform-tools/adb.exe").exists()):
        # try to download it from "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        print("'platform-tools' folder or 'adb.exe' not found")
        if input("Download platform-tools? (y/n) ").lower() == 'y':
            return download_platform_tools()
        else:
            print("Download and extract platform-tools folder from "
                  "https://developer.android.com/studio/releases/platform-tools\n"
                  "Then place the platform-tools folder in the same directory as AutoMonster")
            return False
    return True


def download_platform_tools():
    try:
        download_with_progress("https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
                               "platform-tools.zip")
        print("Extracting...")
        with ZipFile("platform-tools.zip", "r") as zip_ref:
            zip_ref.extractall()
        os.remove("platform-tools.zip")

        if not pathlib.Path("platform-tools/adb.exe").exists():
            raise Exception("platform-tools/adb.exe not found")

        print("Downloaded platform-tools")
    except Exception as e:
        print("Failed to download platform-tools\n"
              "Download and extract platform-tools folder from "
              "https://developer.android.com/studio/releases/platform-tools\n"
              "Then place the platform-tools folder in the same directory as AutoMonster")
        print(e)
        return False
    return True


def download_with_progress(url, file_name):
    u = urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta["Content-Length"])

    block_sz = 8192
    with tqdm(total=file_size, desc=f"Downloading {file_name}", unit_scale=True, unit='B', unit_divisor=1024,
              dynamic_ncols=True) as pbar:
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            f.write(buffer)
            pbar.update(block_sz)
    f.close()


def download_assets():
    # Define the GitHub repository URL
    repo_url = "https://api.github.com/repos/some-guy250/AutoMonster/contents/assets"

    # Send a GET request to the GitHub API to retrieve information about the contents of the "assets" folder
    response = requests.get(repo_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        contents = response.json()

        # Create the "assets" folder if it doesn't exist
        assets_folder = "assets"
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)

        # Iterate through each item in the contents
        for item in tqdm(contents, desc="Downloading assets", unit="file", dynamic_ncols=True):
            # Check if the item is a file
            if item["type"] == "file":
                # Get the download URL for the file
                download_url = item["download_url"]

                # Extract the file name from the URL
                file_name = os.path.basename(download_url)

                # Define the file path to save the file
                file_path = os.path.join(assets_folder, file_name)

                # Send a GET request to download the file
                response = requests.get(download_url)

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(response.content)
    else:
        print(f"Failed to retrieve contents. Status code: {response.status_code}")

# for emulator_path in Emulators.values():
#     if pathlib.Path(emulator_path).exists():
#         Emulator_Path = emulator_path
#         break
# else:
#     raise Exception("No emulator found")
