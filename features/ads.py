import logging
import time
import pathlib
import scrcpy
from Constants import ASSETS, AdLocationsHorizontal, AdLocationsVertical, ADS_DIR, TEAM_SELECTION_THRESHOLD
import AutoMonsterErrors
from utils.logger import setup_logger

logger = setup_logger()

class AdManager:
    def __init__(self, controller):
        self.controller = controller

    def _check_for_common_ads(self):
        screenshot = self.controller.take_screenshot()
        
        ad_keys = self.controller.vision_manager.ad_keys

        if not ad_keys:
            return False

        for ad_key in ad_keys:
            if self.controller.click(ad_key, skip_ad_check=True, threshold=TEAM_SELECTION_THRESHOLD, screenshot=screenshot, gray_img=True):
                self.controller.log_gui(f"Ad detected: {ad_key}", "debug")
                if self.controller.click(ASSETS.ResumeAd, skip_ad_check=True):
                    return None
                return self.controller.in_game()
        return False

    def skip_ad(self) -> bool:
        def check_no_ads():
            if self.controller.in_screen(ASSETS.NoAds, skip_ad_check=True):
                self.controller.click_back(skip_ad_check=True)

        def check_back():
            for _ in range(5):
                if self.controller.in_game():
                    return True
                else:
                    self.controller.click_back(skip_ad_check=True, pause=1.0)
            return self.controller.in_game()

        if self.controller.in_game():
            return False

        counter = 0
        index = 0
        orientation = self.controller.get_orientation()
        max_it = max(len(AdLocationsVertical), len(AdLocationsHorizontal)) * 4

        while not self.controller.in_game():
            if counter > max_it:
                raise AutoMonsterErrors.SkipAdError("Failed to skip ad")

            if self.controller.in_screen(ASSETS.Wheel, skip_ad_check=True, retries=5):
                counter = 0
                break

            if check_back():
                break

            if self._check_for_common_ads():
                check_no_ads()
                logger.info("Skipped common ad")
                return True

            ad_locations = AdLocationsHorizontal
            if orientation == "landscape":
                ad_locations = AdLocationsVertical
                logger.debug("Switched to vertical ad locations")

            if orientation != self.controller.get_orientation():
                orientation = self.controller.get_orientation()
                index = 0
            elif index > len(ad_locations) - 1:
                index = 0

            x, y = ad_locations[index]
            x = self.controller.scale_x(x)
            # y = self.controller.scale_y(y)

            self.controller.client.control.touch(x, y, scrcpy.ACTION_DOWN)
            self.controller.pause(.1)
            self.controller.client.control.touch(x, y, scrcpy.ACTION_UP)

            index += 1
            counter += 1
            self.controller.pause(.25)

        if counter:
            logger.info(f"Skipped ad in {counter} iterations")
            self.controller.click(ASSETS.Exit, skip_ad_check=True)
            check_no_ads()
            return True
        return False

    def _check_for_change(self, t: float = 0):
        sc = self.controller.take_screenshot()
        self.controller.pause(t)
        # Assuming compare_imgs is available or imported. 
        # It was imported from HelperFunctions in AutoMonster.py
        from HelperFunctions import compare_imgs
        return compare_imgs(sc, self.controller.take_screenshot(), transform_to_black=True)

    def _ad_wait_out(self, max_time=18):
        ban = False
        for tick in range(max_time // 2):
            if not ban:
                result = self._check_for_common_ads()
                if result is None:
                    ban = True
                    logger.info("Resumed ad")
                    continue
                if result:
                    logger.info("Skipped common ad in wait")
                    return
                if self._check_for_change(.5):
                    logger.debug("Ad is not moving")
                    return

    def reduce_time(self, max_times: int = 0) -> bool:
        times = 0
        while self.controller.click(ASSETS.ReduceTime, ASSETS.ReduceTimeGold):
            self.controller.pause(2)
            if self.controller.in_game():
                if self.controller.in_screen(ASSETS.ErrorPlayingVideo, screenshot=self.controller.get_last_screenshot()):
                    logger.warning("Error playing video")
                    self.controller.click_back()
                break
            times += 1

            self._ad_wait_out(18)
            self.skip_ad()
            self.controller.wait_for(ASSETS.ReduceTime, ASSETS.ReduceTimeGold, ASSETS.Exit, timeout=5)
            if self.controller.in_screen(ASSETS.Exit, screenshot=self.controller.get_last_screenshot()):
                self.controller.click(ASSETS.Exit, screenshot=self.controller.get_last_screenshot())
                break
            if 0 < max_times <= times:
                break
        return times > 0
