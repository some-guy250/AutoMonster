from typing import List, Callable
import numpy as np
import AutoMonsterErrors
from HelperFunctions import *
from Constants import ASSETS, Ancestral_Cavers, EGGS, AdLocationsHorizontal, AdLocationsVertical, NumberOfCommonAds
import logging
import os


class CustomFormatter(logging.Formatter):
    blue = "\x1b[38;5;4m"
    grey = "\x1b[38;5;7m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    # format levelname message
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
    def __init__(self):
        self.pause = time.sleep
        self.__last_screenshot: Optional[np.ndarray] = None
        # connect to the device
        self.template_dict = {}
        self.device = connect_to_any_device()
        if self.device is None:
            raise AutoMonsterErrors.ConnectError('No device connected')
            # open_emulator()
            # self.pause(5)
            # self.device = connect_to_any_device()
            # if self.device is None:
            #     raise Exception('No device connected')
        logger.info(f'Device connected')

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

        self.open_game(force_close=False)

        self.callable_functions = {
            'do_era_saga': self.do_era_saga,
            'do_pvp': self.do_pvp,
            'reduce_time': self.reduce_time,
        }

    def take_screenshot(self) -> np.ndarray:
        def extract_digit(s: str) -> float:
            return round(int(''.join(filter(str.isdigit, s))) / 1024 / 1024, 2)

        self.__last_screenshot = cv2.imdecode(np.frombuffer(self.device.screencap(), dtype="uint8"), cv2.IMREAD_COLOR)
        # cpu = self.device.shell("top -n 1").split("\n")
        # temp = cpu[1].split(",")
        # total = extract_digit(temp[0])
        # used = extract_digit(temp[1])
        # max_use = [us for us in cpu[5].strip().split(" ") if us != ""]
        # cpu_usage = max_use[8]
        # mem_usage = max_use[9]
        # print(f"Mem usage: {used}/{total}GB")
        # print(f"{max_use[-1].replace('+', '')} is using: Cpu: {cpu_usage}% and Memory: {mem_usage}%")
        # print(f"Screenshot taken in {time.time() - now:.2f} seconds")
        return self.__last_screenshot

    def _get_cords(self, asset_code: str, screenshot=None, threshold=.93, gray_img=False) -> List[List[int]]:
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
            location.append([int(x + w / 1.9), int(y + h / 1.9)])
        return location

    def count(self, *assets, gray_img=False, threshold=.93, screenshot=None):
        if screenshot is None:
            screenshot = self.take_screenshot()
        total = 0
        for a in assets:
            total += len(self._get_cords(a, screenshot, gray_img=gray_img, threshold=threshold))
        return total

    def debug_get_cords_in_image(self, *assets: Optional[str | tuple[str, ...]], display=False) -> List[np.ndarray]:
        screenshot = self.take_screenshot()
        result = []
        for asset in assets:
            cords = self._get_cords(asset, screenshot, gray_img=True)
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
        if display:
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
            cv2.waitKey(0)
        return result

    def click(self, *assets: Optional[str | tuple[str, ...]], skip_ad_check=False, pause: float = 1, screenshot=None,
              raise_error=False, index=0, gray_img=False, threshold=.93) -> bool:
        if screenshot is None:
            screenshot = self.take_screenshot()
        for asset in assets:
            if not self.in_screen(asset, screenshot=screenshot, skip_ad_check=skip_ad_check, gray_img=gray_img,
                                  threshold=threshold):
                continue
            cords = self._get_cords(asset, screenshot, threshold=threshold, gray_img=gray_img)
            if len(cords) > 0:
                x, y = cords[index]
                self.device.input_tap(x, y)
                self.pause(pause)
                return True
        if raise_error:
            raise AutoMonsterErrors.ClickError(f"Could not find any of the assets: {assets}")
        return False

    def click_back(self, skip_ad_check=False):
        if not skip_ad_check and not self.in_game():
            self._skip_ad()
        self.device.input_keyevent("KEYCODE_BACK")
        self.pause(1.5)

    def are_you_there_skip(self, screenshot) -> bool:
        # find slider asset and drag it a bit to the right
        cords = self._get_cords(ASSETS.Slider, screenshot)
        times = 0
        while len(cords) > 0:
            x, y = cords[0]
            self.device.input_swipe(x, y, x + 40, y, 150)
            self.pause(.5)
            times += 1
            if times > 15:
                input("Please move the slider to the right and press enter")
            screenshot = self.take_screenshot()
            if len(con_coord := self._get_cords(ASSETS.Continue, screenshot)) > 0:
                x, y = con_coord[0]
                self.device.input_tap(x, y)
                self.pause(1)
                logger.info("Skipped are you there")
                return True
            cords = self._get_cords(ASSETS.Slider, screenshot)
        return False

    def in_screen(self, *assets: str, screenshot=None, skip_ad_check=False, retries: int = 1, gray_img=False,
                  threshold=.93) -> bool:
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
        return self.in_screen(ASSETS.Cancel, ASSETS.Exit, ASSETS.Battles, ASSETS.Wheel, ASSETS.Shop, ASSETS.StartBattle,
                              ASSETS.AutoBattle, ASSETS.ChangeTeam, ASSETS.SelectTeam, ASSETS.Back, ASSETS.BackPVP,
                              ASSETS.CancelSmall, ASSETS.SpinWheel, ASSETS.ClaimSpin, ASSETS.AreYouThere,
                              ASSETS.PlayCutscene, ASSETS.Skip, ASSETS.AnotherTale, ASSETS.Change,
                              screenshot=screenshot, skip_ad_check=True)

    def wait_for(self, *assets: [str, tuple[str, ...]], timeout: float = 10, skip_ad_check=False,
                 raise_error=False, pause_for: float = 0) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.in_screen(*assets, skip_ad_check=skip_ad_check):
                self.pause(pause_for)
                return True
            self.pause(.5)
        if raise_error:
            raise AutoMonsterErrors.WaitError(f"Could not find any of the assets: {assets} in {timeout} seconds")
        return False

    def follow_sequence(self, *sequence: Optional[Optional[str | tuple[str, ...]]], max_tries: int = 1,
                        reset_func: Optional[Callable] = None, raise_error: bool = False, timeout: float = 5) -> bool:
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
        self.device.shell(r"am force-stop es.socialpoint.MonsterLegends")

    def close_game(self):
        if self.in_game():
            self._goto_islands()
            self.click_back()
            self.click(ASSETS.Yes)
            self.pause(2)
            if self.in_game():
                raise AutoMonsterErrors.CloseGameError("Failed to close game")
        logger.info("Game closed")

    def open_game(self, force_close: bool = True):
        if force_close:
            self.force_close()
            self.pause(2)
        if not self.in_game():
            self.device.shell(r"monkey -p es.socialpoint.MonsterLegends -c android.intent.category.LAUNCHER 1")
        now = time.perf_counter()
        while True:
            if self.in_game():
                break
            if time.perf_counter() - now > 70:
                raise AutoMonsterErrors.OpenGameError("Failed to open game")
            self.pause(1)
        if force_close:
            self.pause(13)
        logger.info("Game opened")

    def _check_for_common_ads(self):
        if self.click(*(f"commonad{i + 1}.png" for i in range(NumberOfCommonAds)), skip_ad_check=True):
            # print("Found common ad")
            # self.pause(1)
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

        def get_orientation():
            if self.device.shell(r"dumpsys input | grep SurfaceOrientation").strip() == "SurfaceOrientation: 3":
                return "portrait"
            return "landscape"

        if self.in_game():
            return False

        counter = 0
        index = 0
        orientation = get_orientation()
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
            if orientation == "portrait":
                ad_locations = AdLocationsVertical

            if orientation != get_orientation():
                orientation = get_orientation()
                index = 0
            elif index > len(ad_locations) - 1:
                index = 0

            pos = ad_locations[index]
            self.device.input_tap(pos[0], pos[1])
            index += 1

            counter += 1
            self.pause(1)

        if counter:
            logger.info(f"Skipped ad in {counter} iterations")
            self.click(ASSETS.Exit, skip_ad_check=True)
            check_no_ads()
            return True
        return False

    def _check_for_change(self, t: float = 0):
        sc = self.take_screenshot()
        self.pause(t)
        return compare_imgs(sc, self.take_screenshot())

    def _ad_wait_out(self, max_time=18):
        # check if dic ad/i exist increment counter until ./ads/i doesn't exist
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
        if not self.follow_sequence(ASSETS.StartBattle, ASSETS.AutoBattle, None):
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
            counter += 1
            if counter > 300:
                raise AutoMonsterErrors.BattleError("Battle is not finished, after 5 minutes")
            self.pause(.5)

    def spin_wheel(self, screenshot=None):
        if self.in_screen(ASSETS.SpinWheel, gray_img=True, threshold=.9, screenshot=screenshot, retries=2):
            self.follow_sequence(ASSETS.SpinWheel, ASSETS.ClaimSpin, ASSETS.Cancel, timeout=15, raise_error=True)
            return True
        return False

    def do_node(self, *, has_wheel: bool, has_cutscene: bool, change_team: bool = False) -> Optional[bool]:
        result = True
        skip_part = False
        # timeout = 5
        timeout = 10

        if has_cutscene:
            if self.in_screen(ASSETS.PlayCutscene):
                while True:
                    if not self.follow_sequence(ASSETS.PlayCutscene, ASSETS.Skip,
                                                (ASSETS.StartBattle, ASSETS.PlayCutscene, ASSETS.EraSagaDone,
                                                 ASSETS.EnterEraSaga), timeout=timeout):
                        if self.in_screen(ASSETS.EraSagaDone, ASSETS.EnterEraSaga):
                            logger.debug("Saved by the bell")
                            return True
                        if not self.in_screen(ASSETS.StartBattle, ASSETS.PlayCutscene):
                            raise AutoMonsterErrors.BattleError("Failed to skip cutscene")
                        logger.debug("Saved by the bell 2")
                    self.pause(2)
                    if self.in_screen(ASSETS.StartBattle):
                        skip_part = True
                        break
                    elif self.in_screen(ASSETS.SagaComplete, ASSETS.EnterEraSaga):
                        return True

        if not skip_part:
            if not self.follow_sequence((ASSETS.EnterBattleRankUp, ASSETS.EnterBattleStamina),
                                        (ASSETS.StartBattle, ASSETS.StartBattleGray, ASSETS.RefillStamina,
                                         ASSETS.NoMonsterLeft, ASSETS.NotFullTeam, ASSETS.NoUndefeated,
                                         ASSETS.SelectTeam, ASSETS.ChangeTeam), timeout=timeout):
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
                            self.pause(60 * 10)
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
                if losses != 0:
                    logger.warning("--------------------")
                losses = 0
            else:
                losses += 1
                logger.warning("Lost a battle")
            if 0 < max_losses <= losses:
                logger.warning("Lost too many battles")
                return False
        return True

    def change_team(self, second_team=False) -> bool:
        def check_and_select_team():
            for index in range(len(selected_team)):
                if self.in_screen(selected_team[index], screenshot=self.__last_screenshot, gray_img=True,
                                  threshold=.92):
                    selected_team.pop(index)
                    non_selected_team.pop(index)
                    return True
            if self.click(*tuple(non_selected_team), screenshot=self.__last_screenshot, gray_img=True, threshold=.92,
                          pause=.5):
                self.take_screenshot()
            for index in range(len(selected_team)):
                if self.in_screen(selected_team[index], screenshot=self.__last_screenshot, gray_img=True,
                                  threshold=.92):
                    selected_team.pop(index)
                    non_selected_team.pop(index)
                    return True
            return False

        def full_team_already_selected():
            screenshot = self.take_screenshot()
            one = min(self.count(ASSETS.Selected1, gray_img=True, screenshot=screenshot), 1)
            two = min(self.count(ASSETS.Selected2, gray_img=True, screenshot=screenshot), 1)
            three = min(self.count(ASSETS.Selected3, gray_img=True, screenshot=screenshot), 1)

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
            ASSETS.RankUp3
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
                ASSETS.RankUp6
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

            if not self.click(ASSETS.Change, screenshot=self.__last_screenshot, index=i):
                return False

            self.take_screenshot()

            if not check_and_select_team():
                for _ in range(6):
                    self.device.input_swipe(300, 200, 300, 800, 300)
                    self.pause(.25)
                self.pause(1)

                for _ in range(50):
                    sc = self.take_screenshot()
                    if check_and_select_team():
                        break
                    self.device.input_swipe(300, 550, 300, 300, 500)
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
        while not self.in_screen(ASSETS.Shop, ASSETS.Settings, ASSETS.Battles, ASSETS.QuitGame):
            self.click(ASSETS.Cancel, ASSETS.CancelSmall, ASSETS.Exit, screenshot=self.__last_screenshot)
            self.click_back()
        self.pause(1)
        if not self.in_screen(ASSETS.QuitGame):
            while not self.in_screen(ASSETS.QuitGame):
                if self.in_screen(ASSETS.HavingFun, screenshot=self.__last_screenshot):
                    self.click(ASSETS.No, screenshot=self.__last_screenshot)
                self.click(ASSETS.Cancel, ASSETS.CancelSmall, screenshot=self.__last_screenshot)
                self.click_back()
        self.click_back()
        logger.info("In islands")

    def _goto_pvp(self):
        attempts = 0
        while True:
            try:
                self.follow_sequence(ASSETS.Battles, ASSETS.EnterMultiplayer, ASSETS.EnterPVP, ASSETS.BattleLog,
                                     reset_func=self._goto_islands, max_tries=3, raise_error=True)
                if not self.in_screen(ASSETS.EnterBattlePVP):
                    self.click_back()
                if self.in_screen(ASSETS.EnterBattlePVP):
                    logger.info("In PVP")
                    break
            except AutoMonsterErrors.AutoMonsterError:
                pass
            attempts += 1
            if attempts == 3:
                raise AutoMonsterErrors.GoToError("Failed to enter PVP")

    def _reduce_egg_time(self) -> Optional[bool]:
        if self.in_screen(ASSETS.EggSpeedup):
            logger.info("Reducing time for egg")
            if not self.in_screen(ASSETS.ReduceTime, ASSETS.ReduceTimeGold, ASSETS.ComeBackLater):
                self.click(ASSETS.EggSpeedup, screenshot=self.__last_screenshot)
            if self.in_screen(ASSETS.ComeBackLater):
                logger.warning("No ads available")
                res = False
            else:
                res = self.reduce_time()
            while not self.in_screen(ASSETS.EnterBattlePVP):
                self.click_back()
            return res
        return None

    def _open_eggs_in_pvp(self) -> bool:
        while self.in_screen(ASSETS.EggDone):
            self.follow_sequence(ASSETS.EggDone, ASSETS.Exit, ASSETS.EnterBattlePVP, raise_error=True,
                                 timeout=10)
            logger.info("Opened egg")
            return True
        return False

    def _start_unlocking_eggs(self) -> bool:
        sc = self.take_screenshot()
        if self._count_eggs(screenshot=sc) == 4:
            if not self.in_screen(ASSETS.EggSpeedup, screenshot=sc) and self.follow_sequence(EGGS,
                                                                                             ASSETS.StartUnlocking,
                                                                                             ASSETS.EnterBattlePVP):
                logger.info("Started unlocking egg")
                return True
        return False

    def _count_eggs(self, screenshot: Optional[np.ndarray] = None) -> int:
        if screenshot is None:
            screenshot = self.take_screenshot()
        if self.in_screen(ASSETS.EggSpeedup, screenshot=screenshot):
            return 0
        return self.count(*EGGS, screenshot=screenshot) + len(self._get_cords(ASSETS.Unlock, screenshot=screenshot))

    def do_pvp(self, num_battles: int = 5, handle_eggs: bool = True, reduce_egg_time: bool = True):
        wins = 0
        losses = 0
        if not self.in_screen(ASSETS.EnterBattlePVP):
            self._goto_pvp()

        while True:
            if not self.in_screen(ASSETS.EnterBattlePVP):
                try:
                    self._goto_pvp()
                except AutoMonsterErrors:
                    raise AutoMonsterErrors.PVPError("Failed to enter PVP")

            if handle_eggs:
                self._start_unlocking_eggs()

                if reduce_egg_time:
                    rd = self._reduce_egg_time()
                    if rd is not None:
                        reduce_egg_time = rd

                self._open_eggs_in_pvp()

            if wins + losses >= num_battles:
                return

            # self.click(ASSETS.EnterBattlePVP)
            self.follow_sequence(ASSETS.EnterBattlePVP, (ASSETS.StartBattle, ASSETS.Yes), timeout=15)
            # self.wait_for(ASSETS.StartBattle, ASSETS.Yes, timeout=15)
            if self.in_screen(ASSETS.Yes, screenshot=self.__last_screenshot):
                self.follow_sequence(ASSETS.Yes, ASSETS.StartBattle, timeout=15)
            self.auto_battle()
            self.click(ASSETS.Cancel, pause=4)
            if self.in_screen(ASSETS.CollectPVP):
                wins += 1
                self.click(ASSETS.CollectPVP, (ASSETS.EnterBattlePVP, ASSETS.SeePVP))
                if not self.in_screen(ASSETS.EnterBattlePVP):
                    self.follow_sequence(ASSETS.BackPVP, ASSETS.DiscardPVP, None)
                counter = 0
                while self.in_screen(ASSETS.SeePVP):
                    if counter > 5:
                        raise Exception('PVP is not working')
                    self.click_back()
            else:
                losses += 1
            print(f'Wins: {wins}, Losses: {losses}')

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
        attempts = 0
        while True:
            try:
                self.follow_sequence(ASSETS.Battles, ASSETS.EnterDungeons, None, reset_func=self._goto_islands,
                                     max_tries=3, raise_error=True)
                if not self.in_screen(ASSETS.Cavern):
                    self.device.input_swipe(500, 200, 100, 200, 200)
                    self.pause(.5)
                self.follow_sequence(ASSETS.Cavern, ASSETS.RightArrow, raise_error=True)
                logger.info("In cavern")
                break
            except AutoMonsterErrors.AutoMonsterError as e:
                print(e)
                pass
            attempts += 1
            if attempts == 3:
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
                if not self.in_screen(ASSETS.EnterCavern):
                    logger.warning("Failed to go back to cavern")
                    self._goto_cavern()
                return True
            return False

        if len(dungeons_to_do) == 0:
            raise AutoMonsterErrors.InputError("No dungeons to do")
        num_dungeons = len(dungeons_to_do)
        dungeons_done = []
        self._goto_cavern()
        sc = self.take_screenshot()
        while self.in_screen(ASSETS.RightArrow, screenshot=sc) and num_dungeons > 0:
            for dungeon in dungeons_to_do:
                if dungeon in dungeons_done or not self.in_screen(dungeon, screenshot=sc):
                    continue

                num_dungeons -= 1
                if self.click(ASSETS.EnterCavern, screenshot=sc):
                    if dungeon in Ancestral_Cavers:
                        if self.in_screen(ASSETS.FlashRaid):
                            self.click(ASSETS.Cancel, screenshot=self.__last_screenshot)
                        else:
                            self.do_dungeon(False, False, False, change_team=change_team)
                        if handle_error_ending(True):
                            break
                    else:
                        sub_dungeons: int = 0
                        while True:
                            for _ in range(2):
                                if self.in_screen(ASSETS.EnterEraSaga):
                                    break
                                self.device.input_swipe(500, 200, 100, 200, 200)
                                self.pause(.5)
                            if not self.click(ASSETS.EnterEraSaga, screenshot=self.__last_screenshot):
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
                if num_dungeons == 0:
                    logger.info("All dungeons done")
                    return
                else:
                    logger.info(f"Finished {dungeon.replace('.png', '')}, {num_dungeons} left")
                dungeons_done.append(dungeon)
            self.click(ASSETS.RightArrow, screenshot=sc)
            sc = self.take_screenshot()

    def play_ads(self):
        played_ads = 0
        errors = 0
        now = time.time()

        while self.in_screen(ASSETS.PlayVideo):
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

            if self.spin_wheel():
                self.pause(1)
                self.take_screenshot()

            if self.in_screen(ASSETS.CollectAd, screenshot=self.__last_screenshot):
                self.click(ASSETS.CollectAd, screenshot=self.__last_screenshot)

        if played_ads == 0:
            logger.info("Didn't play any ads")
        else:
            delta = time.time() - now
            print(f"Finished auto play ads ({played_ads}) {delta // 60}m {delta % 60:.2f}s")

    def do_resource_dungeon(self):
        self.do_dungeon(True, False, True)


def main():
    # set logger level to debug
    # logger.basicConfig(level=logger.DEBUG)

    if not check_platform_tools():
        input("Press enter to exit")
        return

    full_cavers = (
        ASSETS.CavernJestin,
        ASSETS.CavernBaBa,
        ASSETS.CavernKhalorc,
        ASSETS.CavernTyr,
        ASSETS.CavernRobur,
        ASSETS.CavernTheton,
        ASSETS.CavernGriffania,

        ASSETS.CavernGalactic,
        ASSETS.CavernBlossom,
    )

    half_cavers = (
        # ASSETS.CavernMultiverse,
        ASSETS.CavernAlpine,
        ASSETS.CavernAbyssal,
    )

    try:
        controller = Controller()
        # time_function(controller.play_ads)
        # controller.do_dungeon(True, False, True)
        # time_function(controller.reduce_time)
        # time_function(controller.do_era_saga)
        time_function(controller.do_cavern, *full_cavers, change_team=True)
        time_function(controller.do_cavern, *half_cavers, change_team=True, max_rooms=3)
        # time_function(controller.do_pvp, 2)

        # time_function(controller.do_resource_dungeon)

        # controller.close_game()
        # close_emulator()

        # controller.debug_get_cords_in_image(ASSETS.StartBattle, ASSETS.PlayCutscene, ASSETS.EraSagaDone,
        #                                          ASSETS.EnterEraSaga, display=True)
    except Exception as e:
        print(e)
    finally:
        subprocess.Popen(r"platform-tools\adb.exe kill-server", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


if __name__ == '__main__':
    main()
