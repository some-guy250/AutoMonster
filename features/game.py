import time
import logging
from Constants import ASSETS
import AutoMonsterErrors
from utils.logger import setup_logger

logger = setup_logger()

class GameManager:
    def __init__(self, controller):
        self.controller = controller

    def force_close(self):
        self.controller.client.device.shell(r"am force-stop es.socialpoint.MonsterLegends")

    def close_game(self):
        if self.controller.in_game():
            # _goto_islands is likely a method in Controller or another feature. 
            # If it's in Controller, we can call it. If it's in another feature, we might need to rethink.
            # Let's assume it's in Controller for now or we will move it here if it's simple.
            # Checking AutoMonster.py for _goto_islands...
            if hasattr(self.controller, '_goto_islands'):
                self.controller._goto_islands()
            
            self.controller.click_back()
            self.controller.click(ASSETS.Yes)
            self.controller.pause(2)
            if self.controller.in_game():
                raise AutoMonsterErrors.CloseGameError("Failed to close game")
        logger.info("Game closed")

    def launch_game(self):
        self.controller.client.device.shell(r"monkey -p es.socialpoint.MonsterLegends -c android.intent.category.LAUNCHER 1")

    def open_game(self, force_close: bool = True):
        if force_close:
            self.force_close()
            self.controller.pause(2)
        if not self.controller.in_game():
            self.launch_game()
            self.controller.pause(5)
            self.controller.refresh_resolution()
        now = time.perf_counter()
        while True:
            if self.controller.in_game():
                break
            if time.perf_counter() - now > 70:
                raise AutoMonsterErrors.OpenGameError("Failed to open game")
            self.controller.pause(1)
        if force_close:
            self.controller.pause(13)
        self.controller.click(ASSETS.Exit)
        logger.info("Ready to play")

    def _goto_islands(self):
        if not self.controller.in_game():
            self.open_game(force_close=False)
        logger.info("Going to islands")
        count = 0
        while not self.controller.in_screen(ASSETS.QuitGame):
            if self.controller.in_screen(ASSETS.HavingFun):
                self.controller.click(ASSETS.No)
                self.controller.click_back()
            if self.controller.in_screen(ASSETS.ClaimDaily):
                self.controller.click(ASSETS.ClaimDaily)
                self.controller.click_back()
            self.controller.click(ASSETS.Cancel, ASSETS.CancelSmall, ASSETS.Exit, screenshot=self.controller.get_last_screenshot())
            self.controller.click_back()
            count += 1
            if count > 10:
                raise AutoMonsterErrors.GoToError("Failed to go to islands")
        self.controller.pause(1)
        if self.controller.in_screen(ASSETS.QuitGame):
            self.controller.click_back()
        logger.info("In islands")

    def _goto_activity_hub(self):
        if not self.controller.follow_sequence(ASSETS.Battles, ASSETS.ActivityHub, reset_func=self._goto_islands, max_tries=3,
                                    timeout=15,
                                    raise_error=True):
            self.controller.pause(1)
            raise AutoMonsterErrors.GoToError("Failed to enter Activity Hub")

    def scroll_hub(self, asset: str):
        count = 0
        while not self.controller.in_screen(asset):
            self.controller.client.control.swipe(self.controller.scale_x(600), self.controller.scale_y(400), self.controller.scale_x(100), self.controller.scale_y(400), 20)
            self.controller.pause(1)
            count += 1
            if count > 10:
                raise AutoMonsterErrors.GoToError(f"Failed to find {asset} in Activity Hub")
