import logging
import scrcpy
from Constants import ASSETS

logger = logging.getLogger(__name__)


class MonsterManager:
    def __init__(self, controller):
        self.controller = controller
        screen_width, screen_height = self.controller.client.resolution
        self.screen_mid_x = screen_width // 2
        self.scroll_start_y = int(screen_height * 0.55)
        self.scroll_end_y = int(screen_height * 0.25)

    def _scroll_monsters(self):
        """Scroll down to find more monsters"""
        self.controller.client.control.swipe(self.screen_mid_x, self.scroll_start_y, self.screen_mid_x, self.scroll_end_y, move_steps_delay=0.002)
        self.controller.pause(0.5)

    def filter_to_uncommon_monsters(self):
        if not self.controller.in_screen(ASSETS.RarityUCSelected):
            self.controller.follow_sequence((ASSETS.Rarity, ASSETS.RarityRSelected), ASSETS.RarityUC, raise_error=True)
            self.controller.follow_sequence(ASSETS.RarityUC, ASSETS.RarityUCSelected, None, raise_error=True)
        if not self.controller.in_screen(ASSETS.ElementFireSelected):
            self.controller.follow_sequence(ASSETS.Element, ASSETS.ElementFire, raise_error=True)
            self.controller.follow_sequence(ASSETS.ElementFire, ASSETS.ElementFireSelected, None, raise_error=True)

    def filter_to_rare_monsters(self):
        if not self.controller.in_screen(ASSETS.RarityRSelected):
            self.controller.follow_sequence(ASSETS.RarityUCSelected, ASSETS.RarityR, raise_error=True)
            self.controller.follow_sequence(ASSETS.RarityR, ASSETS.RarityRSelected, None, raise_error=True)

    def scroll_until_monster_found(self, monster_asset):
        while not self.controller.in_screen(monster_asset, ASSETS.MonsterEmpty, ASSETS.Unlock):
            self._scroll_monsters()

    def feed_and_sell_monsters(self, num_monsters: int, progress_callback=None):
        self.filter_to_uncommon_monsters()
        num_fed = 0
        monster_asset = ASSETS.MonsterUC
        feeding_list = [(3.5, 3.5), (2.5, 3), (12, 0)]
        while num_fed < num_monsters:
            if progress_callback:
                progress_callback(num_fed / num_monsters)

            if not self.controller.in_screen(monster_asset):
                self.scroll_until_monster_found(monster_asset)
                
                if monster_asset == ASSETS.MonsterR and not self.controller.in_screen(monster_asset, screenshot=self.controller.get_last_screenshot()):
                    logger.info("No more monsters to feed")
                    break

                monster_asset = ASSETS.MonsterR
                feeding_list.pop()
                feeding_list.append((14, 0))
                self.filter_to_rare_monsters()
                self.scroll_until_monster_found(monster_asset)
                if not self.controller.in_screen(monster_asset, screenshot=self.controller.get_last_screenshot()):
                    logger.info("No more monsters to feed")
                    break

            self.controller.follow_sequence(monster_asset, ASSETS.Feed)
            cords = self.controller._get_cords(ASSETS.Feed, screenshot=self.controller.get_last_screenshot())
            if not cords:
                logger.warning("Could not find Feed button")
                break
            x, y = cords[0]

            for hold_time, pause_time in feeding_list:
                self.controller.client.control.touch(x, y, scrcpy.ACTION_DOWN)
                self.controller.pause(hold_time)
                self.controller.client.control.touch(x, y, scrcpy.ACTION_UP)
                self.controller.pause(pause_time)

            self.controller.follow_sequence(ASSETS.MonsterInfo, ASSETS.Sell, ASSETS.Yes, ASSETS.Cancel)
            num_fed += 1
            logger.info(f"Fed and Sold {num_fed} monsters")

        if progress_callback:
            progress_callback(1.0)

    def click_left_moster(self):
        screenshot = self.controller.take_screenshot()
        dino = self.controller._get_cords(ASSETS.HatchDino, screenshot=screenshot) 
        panda = self.controller._get_cords(ASSETS.HatchPanda, screenshot=screenshot)

        if not dino:
            self.controller.click(ASSETS.HatchPanda, pause=1.5, screenshot=screenshot)
        elif not panda:
            self.controller.click(ASSETS.HatchDino, pause=1.5, screenshot=screenshot)
        else:
            if dino[0][0] < panda[0][0]:
                self.controller.click(ASSETS.HatchDino, pause=1.5, screenshot=screenshot)
            else:
                self.controller.click(ASSETS.HatchPanda, pause=1.5, screenshot=screenshot)

        self.controller.click(ASSETS.Place, pause=1.5)

    def breed_monsters(self, num_breeds: int, use_tree: bool = False, progress_callback=None):
        self.controller.zoom_in()

        num_breeds_done = 0
        breader = ASSETS.Tree if use_tree else ASSETS.Mountain

        if progress_callback:
            progress_callback(0)

        max_count = 2
        while num_breeds_done < num_breeds:
            count = 0
            while True:
                while not self.controller.in_screen(ASSETS.Repeat, ASSETS.SpeedUp, pause_for=0):
                    self.controller.click(breader, raise_error=True)
                while not self.controller.in_screen(ASSETS.Repeat, pause_for=0):
                    self.controller.pause(1)
                self.controller.click(ASSETS.Repeat, raise_error=True)
                if count == max_count:
                    break
                self.controller.pause(25)
                self.controller.wait_for(ASSETS.TakeEgg)
                self.controller.click(ASSETS.TakeEgg, pause=1.5)
                if self.controller.in_screen(ASSETS.FullHatchery, pause_for=0):
                    self.controller.click_back()
                    break
                num_breeds_done += 1
                count += 1

            self.controller.click(ASSETS.Hatchery, pause=1.5)
            max_count = -1
            while self.controller.in_screen(ASSETS.HatchDino, ASSETS.HatchPanda, pause_for=0):
                self.click_left_moster()
                timeout = 0
                if not self.controller.in_screen(ASSETS.Place, pause_for=0):
                    while self.controller.in_screen(ASSETS.HatchNotYet, pause_for=0):
                        self.controller.pause(2)
                        timeout += 2
                        if timeout >= 30:
                            raise Exception("Hatching timed out")
                    self.click_left_moster()
                
                self.controller.follow_sequence(ASSETS.PlaceVault, ASSETS.Cancel, timeout=15, raise_error=True)
                self.controller.click_back()
                max_count += 1
            max_count = 2 if max_count > 2 else max_count

            if progress_callback:
                progress_callback(num_breeds_done / num_breeds)

        if progress_callback:
            progress_callback(1.0)
