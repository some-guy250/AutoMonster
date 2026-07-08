"""Handles all game navigation between screens."""

import logging
from typing import TYPE_CHECKING

from utils.assets import ASSETS
from utils.AutoMonsterErrors import *

if TYPE_CHECKING:
    from AutoMonster import Controller

logger = logging.getLogger("AutoMonster")


class Navigator:
    """Handles all game navigation between screens.

    Delegates to the controller for low-level actions (click, wait, follow_sequence)
    and encapsulates the navigation state machines.
    """

    def __init__(self, controller: "Controller"):
        self.controller = controller

    def goto_pvp(self) -> None:
        """Navigate to the PVP battle screen."""
        if self.controller.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
            logger.debug("In PVP")
            return

        self.controller._goto_activity_hub()
        self.controller.scroll_hub(ASSETS.EnterMultiplayer)
        self.controller.follow_sequence(
            ASSETS.EnterMultiplayer, ASSETS.BattleLog, timeout=15
        )
        if not self.controller.wait_for(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints, pause_for=0, timeout=5):
            self.controller.click_back()
        if self.controller.in_screen(ASSETS.EnterBattlePVP, ASSETS.PVPNoPoints):
            logger.debug("In PVP")
        else:
            raise GoToError("Failed to enter PVP")

    def goto_resource_dungeons(self) -> None:
        """Navigate to the resource dungeons screen."""
        self.controller._goto_activity_hub()
        self.controller.scroll_hub(ASSETS.ResourceDungeon)
        self.controller.follow_sequence(ASSETS.ResourceDungeon, ASSETS.EnterCavern)
        logger.debug("In Resource Dungeons")

    def goto_cavern(self) -> None:
        """Navigate to the cavern dungeons screen.

        Raises:
             GoToError: If navigation fails.
        """
        self.controller._goto_activity_hub()
        self.controller.scroll_hub(ASSETS.Cavern)
        if self.controller.follow_sequence(ASSETS.Cavern, ASSETS.RightArrow, timeout=20):
            logger.debug("In cavern")
        else:
            raise GoToError("Failed to enter cavern")
