import time
import logging
from typing import Optional, Tuple
import numpy as np
import cv2
import scrcpy
from adbutils import adb

import AutoMonsterErrors
from utils.logger import setup_logger

logger = setup_logger()

class DeviceManager:
    def __init__(self):
        self.client: Optional[scrcpy.Client] = None
        self.ratio: Optional[Tuple[float, float]] = None
        self.new_width: int = 0
        self.resized: bool = False
        self.__last_screenshot: Optional[np.ndarray] = None
        self._paused: bool = False
        self.cancel_flag: bool = False

        self.connect()

    def pause(self, seconds: float):
        start = time.time()
        while time.time() - start < seconds:
            if self.cancel_flag:
                self.cancel_flag = False
                logger.info("Cancelled current operation in pause")
                raise AutoMonsterErrors.ExecutionFlag
            time.sleep(min(0.1, seconds - (time.time() - start)))

    def connect(self):
        try:
            devices = adb.device_list()
            if not devices:
                raise Exception("No ADB devices found")
            
            self.client = scrcpy.Client(max_fps=10, stay_awake=True, block_frame=True,
                                        device=devices[0])
            self.client.start(True, True)
            logger.info(f'Device connected')
            
            self._check_resolution()
        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            raise e

    def _check_resolution(self):
        size = self.client.resolution
        self.new_width = size[0]
        self.resized = False
        
        if size[0] != 1280 or size[1] != 720:
            self.resized = True
            # Wait for a frame to be available before accessing it
            image = self.client.last_frame
            max_attempts = 10
            attempts = 0
            while image is None and attempts < max_attempts:
                time.sleep(0.1)
                image = self.client.last_frame
                attempts += 1

            if image is None:
                logger.error("Could not get frame from device after 1 second. Device may not be responding.")
                raise Exception("Failed to get frame from device - device connection failed")

            self.new_width = int(720 * image.shape[1] / image.shape[0])
            resized_image = cv2.resize(image, (self.new_width, 720))
            width_original, height_original = image.shape[1], image.shape[0]
            width_resized, height_resized = resized_image.shape[1], resized_image.shape[0]
            self.ratio = (width_original / width_resized, height_original / height_resized)
            logger.info(f"Screen resolution is {size[0]}x{size[1]}, recommended resolution is 1280x720, resizing to "
                        f"{self.new_width}x720 might cause some issues")

    def scale_x(self, x: int) -> int:
        return int(x * self.ratio[0]) if self.resized else x

    def scale_y(self, y: int) -> int:
        return int(y * self.ratio[1]) if self.resized else y

    def get_battery_level(self) -> str:
        return self.client.device.shell("dumpsys battery | grep level").strip().replace("level: ", "")

    def lock_device(self):
        self.client.device.shell("input keyevent 26")

    def get_orientation(self) -> str:
        output = self.client.device.shell(r"dumpsys input | grep SurfaceOrientation").strip()
        if output in ["SurfaceOrientation: 1", "SurfaceOrientation: 3"]:
            return "portrait"
        return "landscape"

    def lower_brightness(self):
        self.client.device.shell("settings put system screen_brightness_mode 0")
        self.client.device.shell("settings put system screen_brightness 0")

    def set_auto_brightness(self):
        self.client.device.shell("settings put system screen_brightness_mode 1")

    def get_brightness_info(self):
        mode = self.client.device.shell("settings get system screen_brightness_mode")
        level = self.client.device.shell("settings get system screen_brightness")
        return mode, level

    def enable_show_taps(self):
        self.client.device.shell("settings put system show_touches 1")

    def disable_show_taps(self):
        self.client.device.shell("settings put system show_touches 0")

    def take_screenshot(self) -> np.ndarray:
        if self.cancel_flag:
            self.cancel_flag = False
            logger.info("Cancelled current operation in take_screenshot")
            raise AutoMonsterErrors.ExecutionFlag

        while self._paused:
            self.pause(5)
            if self.cancel_flag:
                self.cancel_flag = False
                logger.info("Cancelled current operation")
                raise AutoMonsterErrors.ExecutionFlag

        self.__last_screenshot = self.client.last_frame
        if self.resized:
            image = self.__last_screenshot
            new_size = (self.new_width, 720)
            if image.shape[0] > image.shape[1]:
                new_size = (720, self.new_width)
            resized_image = cv2.resize(image, new_size)
            self.__last_screenshot = resized_image
        return self.__last_screenshot

    def get_last_screenshot(self) -> Optional[np.ndarray]:
        return self.__last_screenshot

    def freeze(self):
        self._paused = True

    def unfreeze(self):
        self._paused = False
