import logging
import pathlib
from typing import List, Callable, Optional

import numpy as np
import scrcpy
from adbutils import adb

import AutoMonsterErrors
import Constants
from Constants import ASSETS, Ancestral_Cavers, AdLocationsHorizontal, AdLocationsVertical, NumberOfCommonAds, \
    IN_GAME_ASSETS
from HelperFunctions import *


class CustomFormatter(logging.Formatter):
    blue = "\x1b[38;5;4m"
    grey = "\x1b[38;5;7m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(levelname)s: %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("AutoMonster")
logger.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)
os.system('color')


class Controller:
    def __init__(self, save_screen: bool = False):
        self.gui_logger = None
        self.cancel_flag = False
        self.pause = time.sleep
        self._paused = False
        self.__last_screenshot: Optional[np.ndarray] = None
        # connect to the device
        self.template_dict = {}
        self.client = scrcpy.Client(max_fps=10, stay_awake=True, block_frame=True,
                                    device=adb.device_list()[0])
        self.client.start(True, True)
        self.launch_game()
        time.sleep(2)

        logger.info(f'Device connected')

        size = self.client.resolution
        self.ratio = None
        self.new_width = size[0]
        self.resized = False
        if size[0] != 1280 or size[1] != 720:
            self.resized = True
            image = self.client.last_frame
            self.new_width = int(720 * image.shape[1] / image.shape[0])
            resized_image = cv2.resize(image, (self.new_width, 720))
            width_original, height_original = image.shape[1], image.shape[0]
            width_resized, height_resized = resized_image.shape[1], resized_image.shape[0]
            self.ratio = (width_original / width_resized, height_original / height_resized)
            logger.info(f"Screen resolution is {size[0]}x{size[1]}, recommended resolution is 1280x720, resizing to "
                        f"{self.new_width}x720 might cause some issues")
        self.scale_x = lambda x: int(x * self.ratio[0]) if self.resized else x
        self.scale_y = lambda y: int(y * self.ratio[1]) if self.resized else y

        pathlib.Path('assets').mkdir(parents=True, exist_ok=True)
        self.available_assets: List[str] = []
        for asset in dir(ASSETS):
            if asset.startswith('__'):
                continue
            png_file = getattr(ASSETS, asset)
            if pathlib.Path(f'assets/{png_file}').exists():
                img = cv2.imread(f'assets/{png_file}')
                self.template_dict[png_file] = (img, img.shape[0], img.shape[1])
            else:
                logger.warning(f'Asset {png_file} is missing')

        if save_screen:
            self.save_screen(take_new=True)
        self.open_game(force_close=False)

    def get_battery_level(self):
        return self.client.device.shell("dumpsys battery | grep level").strip().replace("level: ", "")

    def freeze(self):
        self._paused = True

    def unfreeze(self):
        self._paused = False

    def lock_device(self):
        self.client.device.shell("input keyevent 26")

    def get_orientation(self):
        if self.client.device.shell(r"dumpsys input | grep SurfaceOrientation").strip() in ["SurfaceOrientation: 1",
                                                                                            "SurfaceOrientation: 3"]:
            return "portrait"
        return "landscape"

    def lower_brightness(self):
        self.client.device.shell("settings put system screen_brightness_mode 0")
        self.client.device.shell("settings put system screen_brightness 0")

    def set_auto_brightness(self):
        self.client.device.shell("settings put system screen_brightness_mode 1")

    def get_brightness_info(self):
        return self.client.device.shell("settings get system screen_brightness_mode"), self.client.device.shell(
            "settings get system screen_brightness")

    def enable_show_taps(self):
        self.client.device.shell("settings put system show_touches 1")

    def disable_show_taps(self):
        self.client.device.shell("settings put system show_touches 0")

    def log_gui(self, msg, level="info"):
        if self.gui_logger is not None:
            self.gui_logger(msg, level)

    def take_screenshot(self) -> np.ndarray:
        if self.cancel_flag:
            self.cancel_flag = False
            logger.info("Cancelled current operation")
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

    def save_screen(self, name: str = "sc", take_new=False):
        if take_new:
            self.take_screenshot()
        i = 0
        while pathlib.Path(f"sc/{name}{i}.png").exists():
            i += 1
        cv2.imwrite(f"sc/{name}{i}.png", self.__last_screenshot)
        self.log_gui(f"Screenshot saved as {name}{i}.png", "success")

    def _get_cords(self, asset_code: str, screenshot=None, threshold=.9, gray_img=False) -> List[List[int]]:
        if screenshot is None:
            screenshot = self.take_screenshot()
        template, h, w = self.template_dict[asset_code]

        if gray_img:
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

        location = np.where(res >= threshold)

        # rearrange based on the highest value of the match
        location = [(location[0][i], location[1][i]) for i in range(len(location[0]))]
        location.sort(key=lambda pt: res[pt[0]][pt[1]], reverse=True)

        # group the locations that are close to each other by 5px in each direction
        # if the distance between the current location and the last location is less than 5px in each direction
        # then add it to the last location group else create a new group

        location_groups = []
        for loc in location:
            if len(location_groups) == 0:
                location_groups.append([loc])
            else:
                for group in location_groups:
                    if abs(group[-1][0] - loc[0]) < 5 and abs(group[-1][1] - loc[1]) < 5:
                        group.append(loc)
                        break
                else:
                    location_groups.append([loc])

        # update location to be the center of the group
        location = []
        for group in location_groups:
            x = sum(loc[1] for loc in group) // len(group)
            y = sum(loc[0] for loc in group) // len(group)
            # add half the width and height of the template to the location and cast to int
            location.append([self.scale_x(int(x + w / 1.9)), self.scale_y(int(y + h / 1.9))])
        return location

    def count(self, *assets, gray_img=False, threshold=.9, screenshot=None):
        if screenshot is None:
            screenshot = self.take_screenshot()
        total = 0
        for a in assets:
            total += len(self._get_cords(a, screenshot, gray_img=gray_img, threshold=threshold))
        return total

    def debug_get_cords_in_image(self, *assets: Optional[str | tuple[str, ...]], show_asset=False, gray_img=False,
                                 threshold=.9) -> \
            List[np.ndarray]:
        screenshot = self.take_screenshot()
        result = []
        for asset in assets:
            cords = self._get_cords(asset, screenshot, gray_img=gray_img, threshold=threshold)
            if self.resized:
                cords = [[int(x / self.ratio[0]), int(y / self.ratio[1])] for x, y in cords]
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
                cv2.imshow(asset, self.template_dict[asset][0])

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

    def click_back(self, skip_ad_check=False):
        if not skip_ad_check and not self.in_game():
            self._skip_ad()
        self.client.device.keyevent("KEYCODE_BACK")
        self.pause(2)

    def are_you_there_skip(self, screenshot) -> bool:
        # find slider asset and drag it a bit to the right
        cords = self._get_cords(ASSETS.Slider, screenshot)
        times = 0
        while len(cords) > 0:
            x, y = cords[0]
            self.client.control.swipe(x, y, x + 25, y)
            self.pause(.5)
            times += 1
            if times > 30:
                input("Please move the slider to the right and press enter")
            if len(con_coord := self._get_cords(ASSETS.Continue)) > 0:
                x, y = con_coord[0]
                self.client.control.touch(x, y, scrcpy.ACTION_DOWN)
                self.pause(.1)
                self.client.control.touch(x, y, scrcpy.ACTION_UP)
                self.pause(1)
                logger.info("Skipped are you there")
                return True
            cords = self._get_cords(ASSETS.Slider)
        return False

    def in_screen(self, *assets: str, screenshot=None, skip_ad_check=False, retries: int = 1, gray_img=False,
                  threshold=.9) -> bool:
        for _ in range(retries):
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
        return False

    def in_game(self, screenshot: Optional[np.ndarray] = None) -> bool:
        return self.in_screen(*IN_GAME_ASSETS, screenshot=screenshot, skip_ad_check=True)

    def wait_for(self, *assets: [str, tuple[str, ...]], timeout: float = 10, skip_ad_check=False,
                 raise_error=False, pause_for: float = 0) -> bool:
        start_time = time.perf_counter()
        while time.perf_counter() - start_time < timeout:
            if self.in_screen(*assets, skip_ad_check=skip_ad_check):
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
            if not self.click(*action, screenshot=self.__last_screenshot):
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
        self.client.device.shell(r"am force-stop es.socialpoint.MonsterLegends")

    def close_game(self):
        if self.in_game():
            self._goto_islands()
            self.click_back()
            self.click(ASSETS.Yes)
            self.pause(2)
            if self.in_game():
                raise AutoMonsterErrors.CloseGameError("Failed to close game")
        logger.info("Game closed")

    def launch_game(self):
        self.client.device.shell(r"monkey -p es.socialpoint.MonsterLegends -c android.intent.category.LAUNCHER 1")

    def open_game(self, force_close: bool = True):
        if force_close:
            self.force_close()
            self.pause(2)
        if not self.in_game():
            self.launch_game()
        now = time.perf_counter()
        while True:
            if self.in_game():
                break
            if time.perf_counter() - now > 70:
                raise AutoMonsterErrors.OpenGameError("Failed to open game")
            self.pause(1)
        if force_close:
            self.pause(13)
        self.click(ASSETS.Exit)
        logger.info("Ready to play")

    def _check_for_common_ads(self):
        if self.click(*(f"commonad{i + 1}.png" for i in range(NumberOfCommonAds)), skip_ad_check=True):
            if self.click(ASSETS.ResumeAd, skip_ad_check=True):
                return None
            return self.in_game()
        return False

    def _skip_ad(self) -> bool:
        def check_no_ads():
            if self.in_screen(ASSETS.NoAds, skip_ad_check=True):
                self.click_back(skip_ad_check=True)

        def check_back():
            for _ in range(2):
                if self.in_game():
                    return True
                else:
                    self.click_back(skip_ad_check=True)
            return self.in_game()

        if self.in_game():
            return False

        counter = 0
        index = 0
        orientation = self.get_orientation()
        max_it = max(len(AdLocationsVertical), len(AdLocationsHorizontal)) * 4

        while not self.in_game():
            if counter > max_it:
                raise AutoMonsterErrors.SkipAdError("Failed to skip ad")

            if self.in_screen(ASSETS.Wheel, skip_ad_check=True, retries=5):
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
                logger.debug(logging.DEBUG, "Switched to vertical ad locations")

            if orientation != self.get_orientation():
                orientation = self.get_orientation()
                index = 0
            elif index > len(ad_locations) - 1:
                index = 0

            x, y = ad_locations[index]
            x = self.scale_x(x)
            y = self.scale_y(y)

            self.client.control.touch(x, y, scrcpy.ACTION_DOWN)
            self.pause(.1)
            self.client.control.touch(x, y, scrcpy.ACTION_UP)

            index += 1

            counter += 1
            self.pause(1.5)

        if counter:
            logger.info(f"Skipped ad in {counter} iterations")
            self.click(ASSETS.Exit, skip_ad_check=True)
            check_no_ads()
            return True
        return False

    def _check_for_change(self, t: float = 0):
        sc = self.take_screenshot()
        self.pause(t)
        return compare_imgs(sc, self.take_screenshot(), transform_to_black=True)

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
        while self.click(ASSETS.ReduceTime, ASSETS.ReduceTimeGold):
            self.pause(2)
            if self.in_game():
                if self.in_screen(ASSETS.ErrorPlayingVideo, screenshot=self.__last_screenshot):
                    logger.warning("Error playing video")
                    self.click_back()
                break
            times += 1

            self._ad_wait_out(18)
            self._skip_ad()
            self.wait_for(ASSETS.ReduceTime, ASSETS.ReduceTimeGold, ASSETS.Exit, timeout=5)
            if self.in_screen(ASSETS.Exit, screenshot=self.__last_screenshot):
                self.click(ASSETS.Exit, screenshot=self.__last_screenshot)
                break
            if 0 < max_times <= times:
                break
        return times > 0

    def auto_battle(self):
        if not self.follow_sequence((ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.StartBattlePVP),
                                    ASSETS.AutoBattle, None):
            raise AutoMonsterErrors.BattleError("Failed to start battle")
        self.pause(5)
        counter = 5
        while True:
            sc = self.take_screenshot()
            if not self.in_screen(ASSETS.AutoBattle, screenshot=sc) or self.in_screen(ASSETS.Cancel, screenshot=sc):
                # check again because of ancestral monsters >:( they mess up the auto battle
                if self.in_game(screenshot=sc):
                    break
                else:
                    logger.info("Ancestral monster awakened")
            if self.in_screen(ASSETS.NextPVP, screenshot=sc):
                break
            counter += 1
            if counter > 300:
                raise AutoMonsterErrors.BattleError("Battle is not finished, after 5 minutes")
            self.pause(1)

    def spin_wheel(self, screenshot=None):
        if self.in_screen(ASSETS.SpinWheel, gray_img=True, threshold=.9, screenshot=screenshot, retries=2):
            self.follow_sequence(ASSETS.SpinWheel, ASSETS.ClaimSpin, ASSETS.Cancel, timeout=15, raise_error=True)
            return True
        return False

    def do_node(self, *, has_wheel: bool, has_cutscene: bool, change_team: bool = False) -> Optional[bool]:
        result = True
        skip_part = False
        timeout = 12

        if has_cutscene:
            if self.in_screen(ASSETS.PlayCutscene):
                while True:
                    if not self.follow_sequence(ASSETS.PlayCutscene, ASSETS.Skip,
                                                (ASSETS.StartBattle, ASSETS.PlayCutscene, ASSETS.EraSagaDone,
                                                 ASSETS.EnterEraSaga, ASSETS.StartBattleRankUp)):
                        self.wait_for(ASSETS.StartBattleRankUp, ASSETS.StartBattle, timeout=10)
                        if self.in_screen(ASSETS.EraSagaDone, ASSETS.EnterEraSaga):
                            return True
                        if not self.in_screen(ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.PlayCutscene):
                            raise AutoMonsterErrors.BattleError("Failed to skip cutscene")
                    self.pause(3)
                    if self.in_screen(ASSETS.StartBattle, ASSETS.StartBattleRankUp):
                        skip_part = True
                        break
                    elif self.in_screen(ASSETS.SagaComplete, ASSETS.EnterEraSaga):
                        return True

        if not skip_part:
            if not self.follow_sequence((ASSETS.EnterBattleRankUp, ASSETS.EnterBattleStamina),
                                        (ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.StartBattleGray,
                                         ASSETS.RefillStamina, ASSETS.NoMonsterLeft, ASSETS.NotFullTeam,
                                         ASSETS.NoUndefeated, ASSETS.SelectTeam, ASSETS.ChangeTeam), timeout=timeout):
                return None

        if self.in_screen(ASSETS.SelectTeam, screenshot=self.__last_screenshot) and not change_team:
            logger.warning("All monsters are dead and change team is disabled")
            return None

        if self.in_screen(ASSETS.RefillStamina, ASSETS.NoMonsterLeft, ASSETS.NotFullTeam, ASSETS.NoUndefeated,
                          screenshot=self.__last_screenshot):
            return None
        ct = True
        if change_team:
            ct = self.change_team()
        if not ct:
            return None
        if self.in_screen(ASSETS.StartBattleGray):
            return None
        self.auto_battle()
        if has_wheel:
            result = self.spin_wheel(screenshot=self.__last_screenshot)
        self.pause(5)
        return result

    def do_dungeon(self, has_wheel: bool, has_cutscene: bool, has_stamina: bool, *, max_nodes: int = None,
                   max_losses: int = 3, wait_for_stamina_to_refill: bool = True, change_team: bool = False) -> bool:
        nodes = 0
        losses = 0

        while True:
            if not self.wait_for(ASSETS.EnterBattleRankUp, ASSETS.EnterBattleStamina, ASSETS.PlayCutscene):
                break
            if max_nodes is not None and nodes >= max_nodes:
                logger.info("Reached max nodes")
                break
            result = self.do_node(has_wheel=has_wheel, has_cutscene=has_cutscene, change_team=change_team)
            change_team = False
            if result is None:
                waited_for_stamina = False
                if has_stamina:
                    if self.in_screen(ASSETS.RefillStamina, screenshot=self.__last_screenshot):
                        # wait for 10 minutes for stamina to refill
                        logger.warning("Stamina is empty")
                        if wait_for_stamina_to_refill:
                            logger.info("Waiting for stamina to refill")
                            for _ in range(10):
                                self.pause(60)
                                self.take_screenshot()
                            self.click_back()
                            waited_for_stamina = True
                        else:
                            logger.info("Not waiting for stamina to refill")
                            self.click_back()
                            break
                if not waited_for_stamina:
                    break
            elif result:
                nodes += 1
                if losses != 0 and max_losses != 0:
                    logger.info("--------------------")
                losses = 0
            else:
                losses += 1
                if max_losses != 0:
                    logger.warning("Lost a battle")
            if 0 < max_losses <= losses:
                logger.warning("Lost too many battles")
                return False
        return True

    def change_team(self, second_team=False) -> bool:
        def has_selected():
            for index in range(len(selected_team)):
                if self.in_screen(selected_team[index], gray_img=True, threshold=.8):
                    selected_team.pop(index)
                    non_selected_team.pop(index)
                    return True
            return False

        def check_and_select_team():
            if has_selected():
                return True
            self.click(*tuple(non_selected_team), gray_img=True, threshold=.8)
            return has_selected()

        def full_team_already_selected():
            screenshot = self.take_screenshot()
            one = min(self.count(ASSETS.Selected1, gray_img=True, screenshot=screenshot, threshold=.8), 1)
            two = min(self.count(ASSETS.Selected2, gray_img=True, screenshot=screenshot, threshold=.8), 1)
            three = min(self.count(ASSETS.Selected3, gray_img=True, screenshot=screenshot, threshold=.8), 1)

            return one + two + three == 3

        def crop_img(img):
            return img[0: height, 0: width // 3]

        if not self.follow_sequence((ASSETS.SelectTeam, ASSETS.ChangeTeam), ASSETS.Change):
            return False

        height = self.__last_screenshot.shape[0]
        width = self.__last_screenshot.shape[1]

        non_selected_team = [
            ASSETS.RankUp1,
            ASSETS.RankUp2,
            ASSETS.RankUp3,
            ASSETS.RankUp1Synergy,
            ASSETS.RankUp2Synergy,
            ASSETS.RankUp3Synergy
        ]
        selected_team = [
            ASSETS.RankUpSelected1,
            ASSETS.RankUpSelected2,
            ASSETS.RankUpSelected3
        ]

        if second_team:
            non_selected_team = [
                ASSETS.RankUp4,
                ASSETS.RankUp5,
                ASSETS.RankUp6,
                ASSETS.RankUp4Synergy,
                ASSETS.RankUp5Synergy,
                ASSETS.RankUp6Synergy
            ]
            selected_team = [
                ASSETS.RankUpSelected4,
                ASSETS.RankUpSelected5,
                ASSETS.RankUpSelected6
            ]

        for i in range(3):
            if full_team_already_selected():
                self.click_back()
                return True

            if not self.click(ASSETS.Change, index=i):
                return False

            if not check_and_select_team():
                for _ in range(6):
                    self.client.control.swipe(self.scale_x(300), self.scale_y(200), self.scale_x(300),
                                              self.scale_y(800), 20)
                    self.pause(.1)
                self.pause(1)

                for _ in range(50):
                    sc = self.take_screenshot()
                    if check_and_select_team():
                        break
                    self.client.control.swipe(self.scale_x(300), self.scale_y(550), self.scale_x(300),
                                              self.scale_y(300))
                    self.pause(1)
                    if compare_imgs(crop_img(sc), crop_img(self.take_screenshot()), True):
                        logger.warning("Could not find team")
                        return False
            self.click_back()

        self.click_back()

        self.pause(1)
        return True

    def _goto_islands(self):
        if not self.in_game():
            self.open_game(force_close=False)
        logger.info("Going to islands")
        count = 0
        while not self.in_screen(ASSETS.QuitGame):
            if self.in_screen(ASSETS.HavingFun):
                self.click(ASSETS.No)
                self.click_back()
            if self.in_screen(ASSETS.ClaimDaily):
                self.click(ASSETS.ClaimDaily)
                self.click_back()
            self.click(ASSETS.Cancel, ASSETS.CancelSmall, ASSETS.Exit, screenshot=self.__last_screenshot)
            self.click_back()
            count += 1
            if count > 10:
                raise AutoMonsterErrors.GoToError("Failed to go to islands")
        self.pause(1)
        if self.in_screen(ASSETS.QuitGame):
            self.click_back()
        logger.info("In islands")

    def _goto_activity_hub(self):
        if not self.follow_sequence(ASSETS.Battles, ASSETS.ActivityHub, reset_func=self._goto_islands, max_tries=3,
                                    timeout=15,
                                    raise_error=True):
            self.pause(1)
            raise AutoMonsterErrors.GoToError("Failed to enter Activity Hub")

    def scroll_hub(self, asset: str):
        count = 0
        while not self.in_screen(asset):
            self.client.control.swipe(self.scale_x(600), self.scale_y(400), self.scale_x(100), self.scale_y(400))
            self.pause(.1)
            count += 1
            if count > 10:
                raise AutoMonsterErrors.GoToError(f"Failed to scroll to {asset}")

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
            if not self.in_screen(ASSETS.ReduceTime, screenshot=self.__last_screenshot):
                return False
            self.click(ASSETS.BoxSpeedup, screenshot=self.__last_screenshot)
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

    def do_pvp(self, num_battles: int, handle_boxes: bool = True, reduce_box_time: bool = True):
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
                except AutoMonsterErrors:
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
                logger.info(f"Finished PVP, Wins: {wins}, Losses: {losses}")
                self.log_gui(f"Finished PVP, Wins: {wins}, Losses: {losses}")
                return

            if self.in_screen(ASSETS.PVPNoPoints):
                logger.warning("No PVP points stopping early")
                break

            self.follow_sequence(ASSETS.EnterBattlePVP, (ASSETS.StartBattlePVP, ASSETS.Yes), timeout=15)
            if self.in_screen(ASSETS.Yes, screenshot=self.__last_screenshot):
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
                break

    def _goto_cavern(self):
        self._goto_activity_hub()
        self.scroll_hub(ASSETS.Cavern)
        if self.follow_sequence(ASSETS.Cavern, ASSETS.RightArrow, timeout=20):
            logger.info("In cavern")
        else:
            raise AutoMonsterErrors.GoToError("Failed to enter cavern")

    def do_cavern(self, *dungeons_to_do: str, change_team: bool = False, max_rooms: int = 0):
        def handle_error_ending(ancestral: bool) -> bool:
            if self.in_screen(ASSETS.NotFullTeam, ASSETS.NoMonsterLeft, ASSETS.NoUndefeated, ASSETS.StartBattleGray,
                              screenshot=self.__last_screenshot):
                if self.in_screen(ASSETS.StartBattleGray, screenshot=self.__last_screenshot):
                    logger.warning("Cannot start, invalid monsters")
                    self.click_back()
                elif self.in_screen(ASSETS.NotFullTeam, screenshot=self.__last_screenshot):
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
        self._goto_cavern()
        while self.in_screen(ASSETS.RightArrow) and num_dungeons > 0:
            for dungeon in dungeons_to_do:
                if dungeon in dungeons_done or not self.in_screen(dungeon, gray_img=True, threshold=.75):
                    continue

                num_dungeons -= 1
                if self.click(ASSETS.EnterCavern, pause=2):
                    if dungeon in Ancestral_Cavers:
                        if self.wait_for(ASSETS.FlashRaid, timeout=2):
                            logger.info("Ancestral dungeon was already done")
                            self.click(ASSETS.Cancel)
                        else:
                            self.do_dungeon(False, False, False, change_team=change_team)
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
                            if handle_error_ending(False):
                                break
                            sub_dungeons += 1
                            if 0 < max_rooms <= sub_dungeons:
                                logger.info("Reached max rooms")
                                self.click_back()
                                break
                else:
                    logger.warning("Failed to enter cavern")
                self.gui_logger(f"Finished dungeon, {num_dungeons} left")
                if num_dungeons == 0:
                    logger.info("All dungeons done")
                    return
                else:
                    logger.info(f"Finished {dungeon.replace('.png', '')}, {num_dungeons} left")
                dungeons_done.append(dungeon)
            if self.in_screen(ASSETS.DungeonNotAvailable):
                logger.info("Dungeon not available time might be up")
                self.open_game(True)
                break
            self.click(ASSETS.RightArrow, pause=3)

    def play_ads(self):
        played_ads = 0
        errors = 0
        now = time.time()

        while self.wait_for(ASSETS.PlayVideo, timeout=5):
            self.click(ASSETS.PlayVideo, screenshot=self.__last_screenshot)

            self.pause(2)
            if self.in_game():
                if self.in_screen(ASSETS.ErrorPlayingVideo, screenshot=self.__last_screenshot):
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

    def do_resource_dungeons(self):
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
                print(self.do_dungeon(True, False, True, max_losses=0))
            if not self.click(ASSETS.RightArrow, pause=2):
                break
        logger.info("Finished all resource dungeons")

    def seasonal_era_saga(self):
        self.do_dungeon(True, True, False)

    def token_dungeon(self):
        self.do_dungeon(True, False, True)

    def main_loop(self):
        def print_help(cmd: str = None):
            if cmd is None:
                print(Constants.HELP_STRING)
            else:
                if cmd in callable_functions.keys():
                    print(f"\t{Constants.SPECIFIC_HELP_DIC[cmd]}")
                else:
                    print(f"Invalid argument: '{cmd}' for help")

        callable_functions = {
            'era': self.do_era_saga,
            'pvp': self.do_pvp,
            'rd': self.do_resource_dungeons,
            'ads': self.play_ads,
            'cavern': self.do_cavern,
            'help': print_help,
            'version.txt': lambda: print(f"Version: {__version__}"),
        }

        def run_command():
            try:
                callable_functions[command](*args)
                return True
            except AutoMonsterErrors.AutoMonsterError as e:
                print("Error:", e)
                return False

        while True:
            options = ['era', 'pvp', 'resource dungeons', 'ads', 'cavern', 'help', 'version.txt', 'exit']

            # made the options a bit more user-friendly
            print("\nWelcome to AutoMonsters!")
            print("Available commands:")
            for i in options:
                print(f"- {i}")

            raw_command = input("Enter command: ").lower()

            # made a check in case user enters nothing, keep asking until they enter something
            if len(raw_command) == 0:
                print("Please enter a command")
                continue

            command, *args = raw_command.split()

            if command == 'exit':
                break

            if command not in callable_functions.keys():
                print(f"Invalid command: '{command}' type 'help' for a list of commands")
                continue
            try:
                run_command()
            except KeyboardInterrupt:
                print("Command interrupted")


def main():
    controller = Controller()


if __name__ == '__main__':
    main()
