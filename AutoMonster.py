import logging
import pathlib
import sys
from typing import List, Callable, Optional

import numpy as np
import scrcpy
from adbutils import adb

import AutoMonsterErrors
import Constants
from Constants import ASSETS, Ancestral_Cavers, AdLocationsHorizontal, AdLocationsVertical, IN_GAME_ASSETS, ASSET_REGIONS, Region
from HelperFunctions import *
from utils.logger import setup_logger
from utils.vision_manager import VisionManager
from device_manager import DeviceManager
from features.ads import AdManager
from features.game import GameManager
from features.battle import BattleManager

logger = setup_logger()


class Controller:
    def __init__(self, save_screen: bool = False, skip_game_launch: bool = False, serial: Optional[str] = None):
        self.gui_logger = None
        self.device_manager = DeviceManager(serial=serial)
        self.client = self.device_manager.client
        
        self.vision_manager = VisionManager(self.device_manager)

        self.ad_manager = AdManager(self)
        self.game_manager = GameManager(self)
        self.battle_manager = BattleManager(self)

        # Only launch game if not skipping (for faster GUI startup)
        if not skip_game_launch:
            self.launch_game()
            time.sleep(2)

        # insert the ad locations at the beginning of the list
        if self.device_manager.resized:
            size = self.device_manager.client.resolution
            AdLocationsHorizontal.insert(0, (int((size[0] - 130) / self.device_manager.ratio[0]), 85))

        if save_screen:
            self.save_screen(take_new=True)

        # Only open game if not skipping (GUI will handle this later)
        if not skip_game_launch:
            self.open_game(force_close=False)

    def load_templates(self):
        """Reload all templates from disk and Constants.py"""
        self.vision_manager.load_templates()

    def refresh_resolution(self):
        self.device_manager.check_resolution()

    def get_battery_level(self):
        return self.device_manager.get_battery_level()

    def freeze(self):
        self.device_manager.freeze()

    def unfreeze(self):
        self.device_manager.unfreeze()

    def lock_device(self):
        self.device_manager.lock_device()

    def get_orientation(self):
        return self.device_manager.get_orientation()

    def lower_brightness(self):
        self.device_manager.lower_brightness()
        self._brightness_was_lowered = True

    def set_auto_brightness(self):
        self.device_manager.set_auto_brightness()
        self._brightness_was_lowered = False

    def get_brightness_info(self):
        return self.device_manager.get_brightness_info()

    def enable_show_taps(self):
        self.device_manager.enable_show_taps()

    def disable_show_taps(self):
        self.device_manager.disable_show_taps()

    def log_gui(self, msg, level="info"):
        if self.gui_logger is not None:
            self.gui_logger(msg, level)

    def take_screenshot(self) -> np.ndarray:
        return self.device_manager.take_screenshot()

    def get_last_screenshot(self) -> Optional[np.ndarray]:
        return self.device_manager.get_last_screenshot()

    def save_screen(self, name: str = "sc", take_new=False):
        if take_new:
            self.take_screenshot()
            
        # Determine base path to ensure we save next to the executable/script
        if getattr(sys, 'frozen', False):
            base_path = pathlib.Path(sys.executable).parent
        else:
            base_path = pathlib.Path(__file__).parent
            
        sc_dir = base_path / "sc"
        sc_dir.mkdir(exist_ok=True)
        
        i = 0
        while (sc_dir / f"{name}{i}.png").exists():
            i += 1
            
        filepath = sc_dir / f"{name}{i}.png"
        cv2.imwrite(str(filepath), self.device_manager.get_last_screenshot())
        self.log_gui(f"Screenshot saved as {filepath.name}", "success")

    def _get_cords(self, asset_code: str, screenshot=None, threshold=.9, gray_img=False) -> List[List[int]]:
        if screenshot is None:
            screenshot = self.take_screenshot()
        return self.vision_manager.get_cords(asset_code, screenshot, threshold, gray_img)

    def count(self, *assets, gray_img=False, threshold=.9, screenshot=None):
        if screenshot is None:
            screenshot = self.take_screenshot()
        return self.vision_manager.count(*assets, screenshot=screenshot, gray_img=gray_img, threshold=threshold)

    def debug_get_cords_in_image(self, *assets: Optional[str | tuple[str, ...]], show_asset=False, gray_img=False,
                                 threshold=.9) -> \
            List[np.ndarray]:
        screenshot = self.take_screenshot()
        result = []
        for asset in assets:
            cords = self._get_cords(asset, screenshot, gray_img=gray_img, threshold=threshold)
            if self.device_manager.resized:
                cords = [[int(x / self.device_manager.ratio[0]), int(y / self.device_manager.ratio[1])] for x, y in cords]
            colors = [(0, 255, 0)]
            if len(cords) > 1:
                # create a gradient of colors form blue to green in BGR format for each cord
                # make it so that the first cord is blue and the last is green and the rest are in between them
                # the format is BGR
                for i in range(1, len(cords)):
                    blue_component = int(i / (len(cords) - 1) * 255)
                    green_component = int((1 - i / (len(cords) - 1)) * 255)
                    colors.append((blue_component, green_component, 0))

            sc = screenshot.copy()
            if cords is not None:
                for i, (x, y) in enumerate(cords):
                    cv2.circle(sc, (x, y), 7, colors[i], -1)
            result.append(sc)
        images = []
        key = []

        for i in range(0, len(result), 4):
            # stack 2 images horizontally and 2 vertically
            img_num = len(result[i:i + 4])
            filler_img = np.zeros((screenshot.shape[0], screenshot.shape[1], 3), dtype=np.uint8)
            if img_num == 4:
                images.append(np.vstack((np.hstack(result[i:i + 2]), np.hstack(result[i + 2:i + 4]))))
            elif img_num == 3:
                images.append(np.vstack((np.hstack(result[i:i + 2]), np.hstack((result[i + 2], filler_img)))))
            elif img_num == 2:
                images.append(np.hstack(result[i:i + 2]))
            else:
                images.append(result[i])
            if images[-1].shape[0] != screenshot.shape[0]:
                images[-1] = cv2.resize(images[-1], (
                    int(images[-1].shape[1] * screenshot.shape[0] / images[-1].shape[0]), screenshot.shape[0]))
            if images[-1].shape[1] != screenshot.shape[1]:
                images[-1] = cv2.resize(images[-1], (
                    screenshot.shape[1], int(images[-1].shape[0] * screenshot.shape[1] / images[-1].shape[1])))
            key.append(", ".join(assets[i:i + img_num]).replace(".png", ""))

        for i, images in enumerate(images):
            cv2.imshow(f"Assets: {key[i]}", images)

        if show_asset:
            for asset in assets:
                img = self.vision_manager.get_template_image(asset)
                if img is not None:
                    cv2.imshow(asset, img)

        cv2.waitKey(0)
        return result

    def click(self, *assets: Optional[str | tuple[str, ...]], skip_ad_check=False, pause: float = 0.5, screenshot=None,
              raise_error=False, index=0, gray_img=False, threshold=.9) -> bool:
        if screenshot is None:
            screenshot = self.take_screenshot()
        for asset in assets:
            if not self.in_screen(asset, screenshot=screenshot, skip_ad_check=skip_ad_check, gray_img=gray_img,
                                  threshold=threshold):
                continue
            cords = self._get_cords(asset, screenshot, threshold=threshold, gray_img=gray_img)
            if index >= len(cords):
                raise AutoMonsterErrors.ClickError(f"Index {index} is out of range for asset {asset}")
            if len(cords) > 0:
                x, y = cords[index]
                self.client.control.touch(x, y, scrcpy.ACTION_DOWN)
                self.pause(.1)
                self.client.control.touch(x, y, scrcpy.ACTION_UP)
                self.pause(pause)
                return True
        if raise_error:
            raise AutoMonsterErrors.ClickError(f"Could not find any of the assets: {assets}")
        return False

    def click_back(self, skip_ad_check=False, pause: float = 2):
        if not skip_ad_check and not self.in_game():
            self._skip_ad()
        self.client.device.keyevent("KEYCODE_BACK")
        self.pause(pause)

    def are_you_there_skip(self, screenshot) -> bool:
        # find slider asset and drag it a bit to the right
        cords = self._get_cords(ASSETS.Slider, screenshot, threshold=0.8) or self._get_cords(ASSETS.Slider2, screenshot, threshold=0.8)
        times = 0
        while len(cords) > 0:
            x, y = cords[0]
            self.client.control.swipe(x, y, x + 25, y)
            self.pause(.25)
            times += 1
            if times > 50:
                input("Please move the slider to the right and press enter")
            if len(con_coord := self._get_cords(ASSETS.Continue)) > 0:
                x, y = con_coord[0]
                self.client.control.touch(x, y, scrcpy.ACTION_DOWN)
                self.pause(.1)
                self.client.control.touch(x, y, scrcpy.ACTION_UP)
                count = 0
                while True:
                    sc = self.take_screenshot()
                    if len(self._get_cords(ASSETS.Slider, sc, threshold=0.8) + self._get_cords(ASSETS.Slider2, sc, threshold=0.8)) == 0:
                        break
                    self.pause(.5)
                    if count > 5:
                        raise AutoMonsterErrors.SliderError("Slider still present after clicking continue")
                logger.info("Skipped are you there")
                return True
            count = 0
            while True:
                sc = self.take_screenshot()
                cords = self._get_cords(ASSETS.Slider, sc, threshold=0.8) or self._get_cords(ASSETS.Slider2, sc, threshold=0.8)
                if len(cords) != 0:
                    break
                count += 1
                if count > 5:
                    raise AutoMonsterErrors.SliderError("Cannot find slider after trying to move it")
        return False

    def in_screen(self, *assets: str, screenshot=None, skip_ad_check=False, retries: int = 1, gray_img=False,
                  threshold=.9, pause_for=0.5) -> bool:
        for i in range(retries):
            if screenshot is None:
                screenshot = self.take_screenshot()

            if not skip_ad_check and not self.in_game(screenshot):
                if self._skip_ad():
                    screenshot = self.take_screenshot()

            if self.are_you_there_skip(screenshot):
                screenshot = self.take_screenshot()

            for asset in assets:
                if len(self._get_cords(asset, screenshot, threshold=threshold, gray_img=gray_img)) > 0:
                    return True
            screenshot = None
            if i < retries - 1:
                self.pause(pause_for)
        return False

    def in_game(self, screenshot: Optional[np.ndarray] = None) -> bool:
        if screenshot is None:
            screenshot = self.take_screenshot()

        # If width is small, we are likely in portrait mode or bad resize state
        # The game runs in landscape 1280x720.
        if screenshot.shape[1] < 1000:
            return False

        for asset in IN_GAME_ASSETS:
            if len(self._get_cords(asset, screenshot)) > 0:
                return True
        
        return False

    def wait_for(self, *assets: str | tuple[str, ...], timeout: float = 10, skip_ad_check=False,
                 raise_error=False, pause_for: float = 0) -> bool:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            if self.in_screen(*assets, skip_ad_check=skip_ad_check, pause_for=0):
                self.pause(pause_for)
                return True
            self.pause(.1)
        if raise_error:
            raise AutoMonsterErrors.WaitError(f"Could not find any of the assets: {assets} in {timeout} seconds")
        return False

    def follow_sequence(self, *sequence: Optional[Optional[str | tuple[str, ...]]], max_tries: int = 1,
                        reset_func: Optional[Callable] = None, raise_error: bool = False, timeout: float = 7) -> bool:
        # follow sequence of actions, click and wait till then next "thing to click" appears if last is none then
        # don't wait for this to appear else the last one should not be clicked and wait till it appears
        def click_and_wait(action: Optional[str | tuple[str, ...]],
                           next_action: Optional[str | tuple[str, ...]] = None):
            if type(action) is str:
                action = (action,)
            if type(next_action) is str:
                next_action = (next_action,)
            if not self.click(*action, screenshot=self.get_last_screenshot()):
                return False
            if next_action is not None:
                return self.wait_for(*next_action, timeout=timeout)  # , pause_for=.5)
            return True

        # try to follow the sequence up to max_tries times if it fails return False else True
        i = 0
        for tries in range(max_tries):
            if reset_func is not None:
                reset_func()
            # wait for the first action to appear
            sq = sequence[0]
            if type(sq) is str:
                sq = (sq,)

            if not self.wait_for(*sq, timeout=timeout):
                if raise_error:
                    raise AutoMonsterErrors.FollowSequenceError(f"Failed to find first action: {sequence[0]}")
                return False

            for i in range(len(sequence) - 1):
                if not click_and_wait(sequence[i], sequence[i + 1]):
                    break
            else:
                return True
            if tries < max_tries - 1:
                logger.info(f"Failed to follow sequence: {sequence}, trying again")
        if raise_error:
            raise AutoMonsterErrors.FollowSequenceError(f"Failed to follow sequence: {sequence}, in part {sequence[i]}")
        return False

    def force_close(self):
        self.game_manager.force_close()

    def close_game(self, action: str = "Close Game Only"):
        """Close the game and optionally exit program or shutdown computer
        
        Args:
            action: One of:
                - "Close Game Only": Just close the game
                - "Close Game & Exit Program": Close game and exit AutoMonster
                - "Close Game & Shutdown Computer": Close game, exit, and shutdown PC
        """
        import os
        
        self.log_gui("Closing game...", "info")
        self.game_manager.close_game()
        time.sleep(2)  # Give time for the game to close
        
        # Reset brightness before locking device (if it was lowered)
        if hasattr(self, '_brightness_was_lowered') and self._brightness_was_lowered:
            self.set_auto_brightness()
            self.log_gui("Reset device brightness to auto mode", "info")
            self._brightness_was_lowered = False
        
        # Lock device after closing game
        self.log_gui("Locking device...", "info")
        self.lock_device()
        
        if action == "Close Game Only":
            self.log_gui("Game closed and device locked", "success")
            return None
        elif action == "Close Game & Exit Program":
            self.log_gui("Exiting program...", "info")
            return "EXIT"
        elif action == "Close Game & Shutdown Computer":
            self.log_gui("Shutting down computer in 10 seconds...", "warning")
            # Windows shutdown command
            os.system("shutdown /s /t 10")
            self.log_gui("Exiting program...", "info")
            return "EXIT"
        
        return None

    def launch_game(self):
        self.game_manager.launch_game()

    def open_game(self, force_close: bool = True):
        self.game_manager.open_game(force_close)

    def _check_for_common_ads(self):
        return self.ad_manager._check_for_common_ads()

    def _skip_ad(self) -> bool:
        return self.ad_manager.skip_ad()

    def _check_for_change(self, t: float = 0):
        sc = self.take_screenshot()
        self.pause(t)
        return compare_imgs(sc, self.take_screenshot(), transform_to_black=True)

    def _ad_wait_out(self, max_time=18):
        self.ad_manager._ad_wait_out(max_time)

    def reduce_time(self, max_times: int = 0) -> bool:
        return self.ad_manager.reduce_time(max_times)

    def auto_battle(self):
        self.battle_manager.auto_battle()

    def spin_wheel(self, screenshot=None):
        return self.battle_manager.spin_wheel(screenshot)

    def do_node(self, *, has_wheel: bool, has_cutscene: bool, change_team: bool = False) -> Optional[bool]:
        return self.battle_manager.do_node(has_wheel=has_wheel, has_cutscene=has_cutscene, change_team=change_team)

    def do_dungeon(self, has_wheel: bool, has_cutscene: bool, has_stamina: bool, *, max_nodes: int = None,
                   max_losses: int = 3, wait_for_stamina_to_refill: bool = True, change_team: bool = False) -> bool:
        return self.battle_manager.do_dungeon(has_wheel, has_cutscene, has_stamina, max_nodes=max_nodes,
                                              max_losses=max_losses, wait_for_stamina_to_refill=wait_for_stamina_to_refill,
                                              change_team=change_team)

    def change_team(self, second_team=False) -> bool:
        return self.battle_manager.change_team(second_team)

    def _goto_islands(self):
        self.game_manager._goto_islands()

    def _goto_activity_hub(self):
        self.game_manager._goto_activity_hub()

    def scroll_hub(self, asset: str):
        self.game_manager.scroll_hub(asset)

    def _goto_pvp(self):
        self._goto_activity_hub()
        self.scroll_hub(ASSETS.EnterMultiplayer)
        self.follow_sequence(ASSETS.EnterMultiplayer, ASSETS.EnterPVP, ASSETS.BattleLog, timeout=15)
        if not self.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
            self.click_back()
        if self.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
            logger.info("In PVP")

    def _goto_resource_dungeons(self):
        self._goto_activity_hub()
        self.scroll_hub(ASSETS.ResourceDungeon)
        self.follow_sequence(ASSETS.ResourceDungeon, ASSETS.EnterCavern)
        logger.info("In Resource Dungeons")

    def _reduce_box_time(self) -> Optional[bool]:
        if self.in_screen(ASSETS.BoxSpeedup, threshold=.85, gray_img=True):
            logger.info("Reducing time for box")  # Changed from egg to box
            if not self.in_screen(ASSETS.ReduceTime, screenshot=self.get_last_screenshot()):
                return False
            self.click(ASSETS.BoxSpeedup, screenshot=self.get_last_screenshot())
            if self.in_screen(ASSETS.ComeBackLater):
                logger.warning("No ads available")
                res = False
            else:
                res = self.reduce_time()
            while not self.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
                self.click_back()
            return res
        return None

    def _open_pvp_box(self) -> bool:
        while self.in_screen(ASSETS.BoxDone):
            self.follow_sequence(ASSETS.BoxDone, ASSETS.Exit, (ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints),
                                 raise_error=True, timeout=10)
            logger.info("Opened box")  # Changed from egg to box
            return True
        return False

    def _start_unlocking_box(self) -> bool:
        sc = self.take_screenshot()
        if self._can_unlock(screenshot=sc):
            self.follow_sequence(ASSETS.BoxToUnlock, ASSETS.StartUnlocking, (ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints))
            logger.info("Started unlocking box")  # Changed from egg to box
            return True
        return False

    def _can_unlock(self, screenshot: Optional[np.ndarray] = None) -> bool:
        if screenshot is None:
            screenshot = self.take_screenshot()
        if self.in_screen(ASSETS.BoxSpeedup, threshold=.85, gray_img=True, screenshot=screenshot):
            return False
        return self.in_screen(ASSETS.BoxToUnlock, threshold=.85, gray_img=True, screenshot=screenshot)

    def do_pvp(self, num_battles: int, handle_boxes: bool = True, reduce_box_time: bool = True, progress_callback=None):
        wins = 0
        losses = 0

        try:
            num_battles = int(num_battles)
        except ValueError:
            raise AutoMonsterErrors.InputError(f"Invalid number of battles: {num_battles} must be an integer")

        if num_battles < 1:
            raise AutoMonsterErrors.InputError("PVP battles must be greater than 0")

        if not self.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
            self._goto_pvp()

        while True:
            if not self.wait_for(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints, timeout=5):
                try:
                    self._goto_pvp()
                except AutoMonsterErrors.PVPError:
                    raise AutoMonsterErrors.PVPError("Failed to enter PVP")

            if handle_boxes:
                self._start_unlocking_box()

                if reduce_box_time:
                    rd = self._reduce_box_time()
                    if rd is not None:
                        reduce_box_time = rd

                if self._open_pvp_box():
                    self._start_unlocking_box()

            if wins + losses >= num_battles:
                if progress_callback:
                    progress_callback(1.0)
                logger.info(f"Finished PVP, Wins: {wins}, Losses: {losses}")
                self.log_gui(f"Finished PVP, Wins: {wins}, Losses: {losses}")
                return

            if progress_callback:
                progress_callback((wins + losses) / num_battles)

            if self.in_screen(ASSETS.PVPNoPoints):
                logger.warning("No PVP points stopping early")
                break

            self.follow_sequence(ASSETS.EnterBattlePVP, (ASSETS.StartBattlePVP, ASSETS.Yes), timeout=15)
            if self.in_screen(ASSETS.Yes, screenshot=self.get_last_screenshot()):
                self.follow_sequence(ASSETS.Yes, ASSETS.StartBattlePVP, timeout=15)
            self.auto_battle()
            self.click(ASSETS.NextPVP)
            if self.wait_for(ASSETS.CollectPVP, timeout=5):
                wins += 1
                self.click(ASSETS.CollectPVP)
                if self.wait_for(ASSETS.BackPVP, timeout=5):
                    self.follow_sequence(ASSETS.BackPVP, ASSETS.DiscardPVP,
                                         (ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints, ASSETS.SeePVP))
                counter = 0
                while self.in_screen(ASSETS.SeePVP):
                    if counter > 5:
                        raise Exception('PVP is not working')
                    self.click_back()
            else:
                losses += 1
            self.log_gui(f'Wins: {wins}, Losses: {losses}')

    def do_era_saga(self):
        while True:
            sc = self.take_screenshot()
            if self.in_screen(ASSETS.EraSagaDone, screenshot=sc):
                logger.info("Era saga done")
                break
            if not self.in_screen(ASSETS.EnterBattleRankUp, ASSETS.PlayCutscene, screenshot=sc):
                if not self.follow_sequence(ASSETS.EnterEraSaga, (ASSETS.EnterBattleRankUp, ASSETS.PlayCutscene)):
                    logger.warning("Not in era saga")
                    break
            if not self.do_dungeon(True, True, False):
                logger.info("Era saga exiting - reached max losses")
                self.log_gui("Era saga exiting - reached max losses", "warning")
                break

    def _goto_cavern(self):
        self._goto_activity_hub()
        self.scroll_hub(ASSETS.Cavern)
        if self.follow_sequence(ASSETS.Cavern, ASSETS.RightArrow, timeout=20):
            logger.info("In cavern")
        else:
            raise AutoMonsterErrors.GoToError("Failed to enter cavern")

    def do_cavern(self, *dungeons_to_do: str, change_team: bool = False, max_rooms: int = 0, progress_callback=None):
        def handle_error_ending(ancestral: bool) -> bool:
            if self.in_screen(ASSETS.NotFullTeam, ASSETS.NoMonsterLeft, ASSETS.NoUndefeated, ASSETS.StartBattleGray,
                              screenshot=self.get_last_screenshot()):
                if self.in_screen(ASSETS.StartBattleGray, screenshot=self.get_last_screenshot()):
                    logger.warning("Cannot start, invalid monsters")
                    self.click_back()
                elif self.in_screen(ASSETS.NotFullTeam, screenshot=self.get_last_screenshot()):
                    logger.warning("Does not have full team")
                    self.click_back()
                else:
                    logger.warning("No monster left or not enough undefeated")
                for _ in range(1 if ancestral else 2):
                    self.click_back()
                if not self.wait_for(ASSETS.EnterCavern, timeout=5):
                    logger.warning("Failed to go back to cavern")
                    self._goto_cavern()
                return True
            return False

        if len(dungeons_to_do) == 0:
            raise AutoMonsterErrors.InputError("No dungeons to do")

        dungeons_to_do_temp = []
        for dungeon in set(dungeons_to_do):
            if dungeon not in Constants.CAVERN_TO_ASSETS.keys():
                logger.warning(f"Invalid dungeon: {dungeon}")
            else:
                dungeons_to_do_temp.append(Constants.CAVERN_TO_ASSETS[dungeon])
        dungeons_to_do = dungeons_to_do_temp

        num_dungeons = len(dungeons_to_do)
        dungeons_done = []
        total_rooms_done = 0
        total_expected_rooms = max_rooms * num_dungeons  # Calculate total expected rooms

        self._goto_cavern()
        while self.in_screen(ASSETS.RightArrow) and num_dungeons > 0:
            for dungeon in dungeons_to_do:
                if dungeon in dungeons_done or not self.in_screen(dungeon, gray_img=True, threshold=.75):
                    continue

                if self.click(ASSETS.EnterCavern, pause=2):
                    if dungeon in Ancestral_Cavers:
                        if self.wait_for(ASSETS.FlashRaid, timeout=2):
                            logger.info("Ancestral dungeon was already done")
                            self.click(ASSETS.Cancel)
                            total_rooms_done += max_rooms  # Count all rooms for completed ancestral
                        else:
                            self.do_dungeon(False, False, False, change_team=change_team)
                            total_rooms_done += 1  # Count ancestral as 1 room
                        if handle_error_ending(True):
                            break
                    else:
                        sub_dungeons: int = 0
                        while True:
                            for _ in range(3):
                                if self.wait_for(ASSETS.EnterEraSaga, timeout=3):
                                    break
                                self.client.control.swipe(self.scale_x(500), self.scale_y(200), self.scale_x(100),
                                                          self.scale_y(200))
                                self.pause(1)
                            if not self.click(ASSETS.EnterEraSaga):
                                self.click_back()
                                if self.in_screen(ASSETS.EnterCavern):
                                    break
                                logger.warning("Failed to go back to cavern")
                                self._goto_cavern()
                                break
                            self.do_dungeon(False, False, False, change_team=change_team)
                            sub_dungeons += 1
                            total_rooms_done += 1
                            if progress_callback:
                                progress_callback(min(total_rooms_done / total_expected_rooms, 1.0))
                            if handle_error_ending(False):
                                break
                            if 0 < max_rooms <= sub_dungeons:
                                logger.info("Reached max rooms")
                                self.click_back()
                                break
                else:
                    logger.warning("Failed to enter cavern")

                num_dungeons -= 1
                if progress_callback:
                    # Ensure progress shows at least the completion of current dungeon
                    min_progress = (len(dungeons_done) + 1) / len(dungeons_to_do)
                    actual_progress = total_rooms_done / total_expected_rooms
                    progress_callback(max(min_progress, actual_progress))

                self.log_gui(f"Finished dungeon, {num_dungeons} left")
                if num_dungeons == 0:
                    logger.info("All dungeons done")
                    if progress_callback:
                        progress_callback(1.0)
                    return
                else:
                    logger.info(f"Finished {dungeon.replace('.png', '')}, {num_dungeons} left")
                dungeons_done.append(dungeon)

            if self.in_screen(ASSETS.DungeonNotAvailable):
                logger.info("Dungeon not available time might be up")
                self.open_game(True)
                break
            self.click(ASSETS.RightArrow, pause=3)

        # Ensure progress shows complete even if we finish early
        if progress_callback:
            progress_callback(1.0)

    def play_ads(self):
        played_ads = 0
        errors = 0
        now = time.time()

        while self.wait_for(ASSETS.PlayVideo, timeout=5):
            self.click(ASSETS.PlayVideo, screenshot=self.get_last_screenshot())

            self.pause(3)
            if self.in_game():
                if self.in_screen(ASSETS.ErrorPlayingVideo, screenshot=self.get_last_screenshot()):
                    logger.warning("Error playing video")
                    errors += 1
                    self.click_back()
                    if errors > 3:
                        raise AutoMonsterErrors.PlayAdsError("Error playing video")
                    continue
                else:
                    raise AutoMonsterErrors.PlayAdsError("Failed to play ad")

            errors = 0
            played_ads += 1

            self._ad_wait_out(18)
            self._skip_ad()
            self.pause(1)

            self.spin_wheel()
            self.pause(1)

            self.click(ASSETS.CollectAd)

        if played_ads == 0:
            logger.info("Didn't play any ads")
        else:
            delta = time.time() - now
            print(f"Finished auto play ads ({played_ads}) {delta // 60}m {delta % 60:.2f}s")

    def do_resource_dungeons(self, wait_for_stamina_to_refill=False):
        self._goto_resource_dungeons()

        while True:
            if self.in_screen(ASSETS.GemDungeon, ASSETS.RuneDungeon, ASSETS.MazeCoinDungeon):
                if self.in_screen(ASSETS.GemDungeon):
                    logger.info("Entering gem dungeon")
                elif self.in_screen(ASSETS.RuneDungeon):
                    logger.info("Entering rune dungeon")
                elif self.in_screen(ASSETS.MazeCoinDungeon):
                    logger.info("Entering maze coin dungeon")
                self.click(ASSETS.EnterCavern)
                print(self.do_dungeon(True, False, True, max_losses=-1,
                                      wait_for_stamina_to_refill=wait_for_stamina_to_refill))
            if not self.click(ASSETS.RightArrow, pause=2):
                break
        logger.info("Finished all resource dungeons")

    def scale_x(self, x):
        return self.device_manager.scale_x(x)

    def scale_y(self, y):
        return self.device_manager.scale_y(y)

    @property
    def new_width(self):
        return self.device_manager.new_width

    @property
    def cancel_flag(self):
        return self.device_manager.cancel_flag

    @cancel_flag.setter
    def cancel_flag(self, value):
        self.device_manager.cancel_flag = value

    def pause(self, seconds: float):
        self.device_manager.pause(seconds)

    @property
    def resized(self):
        return self.device_manager.resized

    @property
    def ratio(self):
        return self.device_manager.ratio


def main():
    controller = Controller()
    controller.change_team()


if __name__ == '__main__':
    main()
