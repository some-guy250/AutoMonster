import logging
import scrcpy
from utils.assets import ASSETS, RUNE_LEVEL_TO_ASSET, RUNE_TYPE_TO_ASSET, get_rune_asset
from config.config import SCROLL_START_Y_FRACTION

logger = logging.getLogger(__name__)


class MonsterManager:
    def __init__(self, controller):
        self.controller = controller
        screen_width, screen_height = self.controller.client.resolution
        self.screen_mid_x = screen_width // 2
        self.scroll_start_y = int(screen_height * SCROLL_START_Y_FRACTION)
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

    def feed_and_sell_monsters(self):
        self.filter_to_uncommon_monsters()
        num_fed = 0
        monster_asset = ASSETS.MonsterUC
        feeding_list = [(4.5, 3), (3.5, 3), (12, 0)]
        while True:
            if not self.controller.in_screen(monster_asset):
                self.scroll_until_monster_found(monster_asset)
                
                if monster_asset == ASSETS.MonsterR and not self.controller.in_screen(monster_asset, screenshot=self.controller.get_last_screenshot()):
                    logger.debug("No more monsters to feed")
                    break

                monster_asset = ASSETS.MonsterR
                feeding_list.pop()
                feeding_list.append((14, 0))
                self.filter_to_rare_monsters()
                self.scroll_until_monster_found(monster_asset)
                if not self.controller.in_screen(monster_asset, screenshot=self.controller.get_last_screenshot()):
                    logger.debug("No more monsters to feed")
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

            self.controller.follow_sequence(ASSETS.MonsterInfo, ASSETS.SellOwned, ASSETS.Yes, ASSETS.Cancel)
            num_fed += 1
            logger.debug(f"Fed and Sold {num_fed} monsters")

    def click_left_moster(self, sell: bool = False):
        screenshot = self.controller.take_screenshot()
        dino = self.controller._get_cords(ASSETS.HatchDino, screenshot=screenshot) 
        panda = self.controller._get_cords(ASSETS.HatchPanda, screenshot=screenshot)

        if not dino:
            self.controller.click(ASSETS.HatchPanda, screenshot=screenshot)
        elif not panda:
            self.controller.click(ASSETS.HatchDino, screenshot=screenshot)
        else:
            if dino[0][0] < panda[0][0]:
                self.controller.click(ASSETS.HatchDino, screenshot=screenshot)
            else:
                self.controller.click(ASSETS.HatchPanda, screenshot=screenshot)

        self.controller.pause(1.5)

        if not sell:
            self.controller.click(ASSETS.Place, pause=1.5)

    def breed_monsters(self, num_breeds: int, use_tree: bool = False, feed_and_sell_monsters: bool = False, sell: bool = False, batch_size: int = 15, progress_callback=None):
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
                count += 1

            self.controller.click(ASSETS.Hatchery, pause=1.5)
            max_count = -1
            number_of_monsters = self.controller.count(ASSETS.HatchDino, ASSETS.HatchPanda)
            while self.controller.in_screen(ASSETS.HatchDino, ASSETS.HatchPanda, pause_for=0):
                self.click_left_moster(sell=sell)
                timeout = 0
                if not self.controller.in_screen(ASSETS.Place, pause_for=0):
                    while self.controller.in_screen(ASSETS.HatchNotYet, pause_for=0):
                        self.controller.pause(2)
                        timeout += 2
                        if timeout >= 30:
                            raise Exception("Hatching timed out")
                    self.click_left_moster(sell=sell)
                
                num_breeds_done += 1
                max_count += 1
                if progress_callback:
                    progress_callback(num_breeds_done / num_breeds)
                if sell:
                    self.controller.follow_sequence(ASSETS.Sell, ASSETS.Yes, ASSETS.Hatchery)
                else:
                    self.controller.follow_sequence(ASSETS.PlaceVault, ASSETS.Cancel, timeout=15, raise_error=True)
                    if feed_and_sell_monsters and (num_breeds_done % batch_size == 0 or (max_count + 1 == number_of_monsters and num_breeds_done >= num_breeds)):
                        self.feed_and_sell_monsters()
                    self.controller.click_back()
            max_count = 2 if max_count > 2 else max_count

        if progress_callback:
            progress_callback(1.0)

    def craft_runes(self, num_runes: int, level: str = "I", rune_type: str = "Life", team: bool = False, progress_callback=None):
        """Craft runes for monsters.
        
        Args:
            num_runes: Number of runes to craft
            level: Rune level (Roman numeral: I, II, III, IV, V)
            rune_type: Type of rune (Life, Strength, Stamina, Speed, Gold)
            team: Whether to craft for team monsters
            progress_callback: Optional callback(progress, message) for progress updates
        """
        # Roman numeral to int mapping
        roman_to_int = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
        level_int = roman_to_int.get(level, 1)
        
        try:
            level_asset = RUNE_LEVEL_TO_ASSET.get(level_int, ASSETS.RuneLevel1)
            type_asset = RUNE_TYPE_TO_ASSET.get(rune_type, ASSETS.RuneLife)
            
            if not self.controller.in_screen(level_asset, pause_for=0):
                self.controller.click(ASSETS.RuneLevel, raise_error=True)
                self.controller.pause(1)
            self.controller.click(level_asset, raise_error=True)
            self.controller.click(ASSETS.RuneType, raise_error=True)
            self.controller.pause(1)
            self.controller.click(type_asset, raise_error=True)
            
            self.controller.click(ASSETS.RuneType, raise_error=True)
            
            rune_asset = get_rune_asset(level_int, rune_type, team)
            logger.info(f"Crafting {num_runes} runes: {rune_asset}")
            
            if progress_callback:
                progress_callback(0)
            
            for rune_num in range(num_runes):
                logger.debug(f"  Rune {rune_num+1}/{num_runes}")
                
                if progress_callback:
                    progress_callback((rune_num + 1) / num_runes)
                
                for drag_num in range(4):
                    sc = self.controller.take_screenshot()
                    
                    if not self.controller.in_screen(rune_asset, screenshot=sc):
                        logger.debug(f"    Drag {drag_num+1}: Rune not found, stopping")
                        raise Exception(f"Rune {rune_asset} not found on screen, cannot craft rune.")
                    
                    self.controller.drag(rune_asset, ASSETS.RuneDrop, screenshot=sc)
                    self.controller.pause(0.25)

                # Craft the rune
                self.controller.wait_for(ASSETS.RuneCraft, timeout=5, raise_error=True)
                self.controller.click(ASSETS.RuneCraft, screenshot=self.controller.get_last_screenshot())
                while not self.controller.click(ASSETS.RuneCollect):
                    self.controller.pause(5)

                logger.info(f"Crafted rune {rune_num+1}/{num_runes}: {rune_asset}")
            
            if progress_callback:
                progress_callback(1.0)
            
        except Exception as e:
            logger.error(f"Error crafting runes: {e}")
            raise
