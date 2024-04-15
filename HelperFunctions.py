import os
import sys
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
from tempfile import gettempdir

# Emulator_Path: str | None = None

repo_url_api = "https://api.github.com/repos/some-guy250/AutoMonster"
repo_url = "https://github.com/some-guy250/AutoMonster"


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

    # Send a GET request to the GitHub API to retrieve information about the contents of the "assets" folder
    response = requests.get(f"{repo_url_api}/contents/assets")

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


def compare_versions(version1, version2):
    v1_parts = version1.split('.')
    v2_parts = version2.split('.')

    # Compare each part of the version number
    for i in range(max(len(v1_parts), len(v2_parts))):
        v1_part = int(v1_parts[i]) if i < len(v1_parts) else 0
        v2_part = int(v2_parts[i]) if i < len(v2_parts) else 0

        if v1_part < v2_part:
            return -1
        elif v1_part > v2_part:
            return 1

    # All parts are equal, versions are the same
    return 0


def check_for_updates(current_version: str):
    response = requests.get(f"{repo_url_api}/releases/latest")
    latest_release = response.json()
    latest_version = latest_release['tag_name'].replace("v-", "")
    if compare_versions(latest_version, current_version) == 1:
        print(f"New version available: v-{latest_version}")
        # check if it's the exe
        if sys.argv[0].endswith(".exe"):
            if input("Download update? (y/n): ").lower() == 'y':
                download_update()
            else:
                print(f"Download the update from the releases page: {repo_url}/releases")
        else:
            print(f"Clone the repository to get the latest version")
            print(f"git clone {repo_url}.git")


def download_update():
    response = requests.get(f"{repo_url_api}/releases/latest")
    latest_release = response.json()
    assets = latest_release['assets']
    asset_url = assets[0]['browser_download_url']
    name = assets[0]['name']
    temp_dir = gettempdir()
    print(f"Update downloaded to {temp_dir})")
    download_with_progress(asset_url, f"{temp_dir}/{name}")
    # extract the zip file
    with ZipFile(f"{temp_dir}/{name}", "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    # delete the zip file
    os.remove(f"{temp_dir}/{name}")

    # delete the assets folder and everything in it
    if os.path.exists("assets"):
        for file in os.listdir("assets"):
            os.remove(f"assets/{file}")
        os.rmdir("assets")

    # create a batch file to delete the old "AutoMonster.exe" and replace it with the new one in the temp directory
    # make it so the bat waits for AutoMonster to close before replacing it, a new terminal window should open
    # detached from the current one so this one can close
    bat = f"""@echo off
    taskkill /f /im AutoMonster.exe >nul 2>&1
    if exist "{os.path.abspath("AutoMonster.exe")}" (
        del "{os.path.abspath("AutoMonster.exe")}"
    )
    move "{os.path.abspath(f"{temp_dir}/AutoMonster.exe")}" "{os.path.abspath("AutoMonster.exe")}"
    start AutoMonster.exe --update
    del "{os.path.abspath(f"{temp_dir}/update.bat")}"
    """
    with open(f"{temp_dir}/update.bat", "w") as f:
        f.write(bat)
    # run the batch file and close the current instance of AutoMonster
    subprocess.Popen(f"{temp_dir}/update.bat", creationflags=subprocess.CREATE_NEW_CONSOLE)
    exit()

# for emulator_path in Emulators.values():
#     if pathlib.Path(emulator_path).exists():
#         Emulator_Path = emulator_path
#         break
# else:
#     raise Exception("No emulator found")
