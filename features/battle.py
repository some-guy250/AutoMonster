import logging
from typing import Optional
from Constants import ASSETS
import AutoMonsterErrors
from utils.logger import setup_logger

logger = setup_logger()

class BattleManager:
    def __init__(self, controller):
        self.controller = controller

    def auto_battle(self):
        if not self.controller.follow_sequence((ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.StartBattlePVP),
                                    ASSETS.AutoBattle, None):
            raise AutoMonsterErrors.BattleError("Failed to start battle")
        self.controller.pause(5)
        counter = 5
        while True:
            sc = self.controller.take_screenshot()
            if not self.controller.in_screen(ASSETS.AutoBattle, screenshot=sc) or self.controller.in_screen(ASSETS.Cancel, screenshot=sc):
                # check again because of ancestral monsters >:( they mess up the auto battle
                if self.controller.in_game(screenshot=sc):
                    break
                else:
                    logger.info("Ancestral monster awakened")
            if self.controller.in_screen(ASSETS.NextPVP, screenshot=sc):
                break
            counter += 1
            if counter > 300:
                raise AutoMonsterErrors.BattleError("Battle is not finished, after 5 minutes")
            self.controller.pause(1)

    def spin_wheel(self, screenshot=None):
        if self.controller.in_screen(ASSETS.SpinWheel, gray_img=True, threshold=.9, screenshot=screenshot, retries=2):
            self.controller.follow_sequence(ASSETS.SpinWheel, ASSETS.ClaimSpin, ASSETS.Cancel, timeout=15, raise_error=True)
            return True
        return False

    def change_team(self, second_team=False) -> bool:
        def has_selected():
            for index in range(len(selected_team)):
                if self.controller.in_screen(selected_team[index], gray_img=True, threshold=.8):
                    selected_team.pop(index)
                    non_selected_team.pop(index)
                    non_selected_team_synergy.pop(index)
                    return True
            return False

        def check_and_select_team():
            if has_selected():
                return True
            if not self.controller.click(*non_selected_team, gray_img=True, threshold=.8):
                self.controller.click(*non_selected_team_synergy, gray_img=True, threshold=.8)
            return has_selected()

        def full_team_already_selected():
            screenshot = self.controller.take_screenshot()
            one = min(self.controller.count(ASSETS.Selected1, gray_img=True, screenshot=screenshot, threshold=.8), 1)
            two = min(self.controller.count(ASSETS.Selected2, gray_img=True, screenshot=screenshot, threshold=.8), 1)
            three = min(self.controller.count(ASSETS.Selected3, gray_img=True, screenshot=screenshot, threshold=.8), 1)

            return one + two + three == 3

        def crop_img(img):
            return img[0: height, 0: width // 3]

        if not self.controller.follow_sequence((ASSETS.SelectTeam, ASSETS.ChangeTeam), ASSETS.Change):
            return False

        height = self.controller.get_last_screenshot().shape[0]
        width = self.controller.get_last_screenshot().shape[1]

        non_selected_team = [
            ASSETS.RankUp1,
            ASSETS.RankUp2,
            ASSETS.RankUp3,
        ]
        non_selected_team_synergy = [
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
            ]
            non_selected_team_synergy = [
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
                self.controller.click_back()
                return True

            if not self.controller.click(ASSETS.Change, index=i):
                return False

            if not check_and_select_team():
                for _ in range(6):
                    self.controller.client.control.swipe(self.controller.scale_x(300), self.controller.scale_y(200), self.controller.scale_x(300),
                                              self.controller.scale_y(800), 20)
                    self.controller.pause(.1)
                self.controller.pause(1)

                for _ in range(50):
                    sc = self.controller.take_screenshot()
                    if check_and_select_team():
                        break
                    self.controller.client.control.swipe(self.controller.scale_x(300), self.controller.scale_y(550), self.controller.scale_x(300),
                                              self.controller.scale_y(300))
                    self.controller.pause(.5)
                    # Assuming compare_imgs is available. It needs to be imported.
                    from HelperFunctions import compare_imgs
                    if compare_imgs(crop_img(sc), crop_img(self.controller.take_screenshot()), True):
                        logger.warning("Could not find team")
                        self.controller.log_gui("Could not find team", "warning")
                        return False
            self.controller.click_back()

        self.controller.click_back()
        return True

    def do_node(self, *, has_wheel: bool, has_cutscene: bool, change_team: bool = False) -> Optional[bool]:
        result = True
        skip_part = False
        timeout = 12

        if has_cutscene:
            if self.controller.in_screen(ASSETS.PlayCutscene):
                while True:
                    if not self.controller.follow_sequence(ASSETS.PlayCutscene, ASSETS.Skip,
                                                (ASSETS.StartBattle, ASSETS.PlayCutscene, ASSETS.EraSagaDone,
                                                 ASSETS.EnterEraSaga, ASSETS.StartBattleRankUp)):
                        self.controller.wait_for(ASSETS.StartBattleRankUp, ASSETS.StartBattle, timeout=15)
                        if self.controller.in_screen(ASSETS.EraSagaDone, ASSETS.EnterEraSaga, reties=3):
                            return True
                        if not self.controller.in_screen(ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.PlayCutscene, reties=3):
                            raise AutoMonsterErrors.BattleError("Failed to skip cutscene")
                    self.controller.pause(3)
                    if self.controller.in_screen(ASSETS.StartBattle, ASSETS.StartBattleRankUp):
                        skip_part = True
                        break
                    elif self.controller.in_screen(ASSETS.SagaComplete, ASSETS.EnterEraSaga):
                        return True

        if not skip_part:
            if not self.controller.follow_sequence((ASSETS.EnterBattleRankUp, ASSETS.EnterBattleStamina),
                                        (ASSETS.StartBattle, ASSETS.StartBattleRankUp, ASSETS.StartBattleGray,
                                         ASSETS.RefillStamina, ASSETS.NoMonsterLeft, ASSETS.NotFullTeam,
                                         ASSETS.NoUndefeated, ASSETS.SelectTeam, ASSETS.ChangeTeam), timeout=timeout):
                return None

        if self.controller.in_screen(ASSETS.SelectTeam, screenshot=self.controller.get_last_screenshot()) and not change_team:
            logger.warning("All monsters are dead and change team is disabled")
            return None

        if self.controller.in_screen(ASSETS.RefillStamina, ASSETS.NoMonsterLeft, ASSETS.NotFullTeam, ASSETS.NoUndefeated,
                          screenshot=self.controller.get_last_screenshot()):
            return None
        ct = True
        if change_team:
            # We need to implement change_team in this class or call it from controller if it's still there.
            # I'll assume for now we call the one in this class (which currently calls controller)
            # But wait, if I move it here, I should implement it here.
            # I'll leave it as self.controller.change_team for now to avoid breaking if I don't move it yet.
            ct = self.controller.change_team()
        if not ct:
            return None
        if self.controller.in_screen(ASSETS.StartBattleGray):
            return None
        self.auto_battle()
        if has_wheel:
            result = self.spin_wheel(screenshot=self.controller.get_last_screenshot())
        self.controller.pause(5)
        return result

    def do_dungeon(self, has_wheel: bool, has_cutscene: bool, has_stamina: bool, *, max_nodes: int = None,
                   max_losses: int = 3, wait_for_stamina_to_refill: bool = True, change_team: bool = False) -> bool:
        nodes = 0
        losses = 0

        while True:
            if not self.controller.wait_for(ASSETS.EnterBattleRankUp, ASSETS.EnterBattleStamina, ASSETS.PlayCutscene):
                break
            if max_nodes is not None and nodes >= max_nodes:
                logger.info("Reached max nodes")
                break
            result = self.do_node(has_wheel=has_wheel, has_cutscene=has_cutscene, change_team=change_team)
            change_team = False
            if result is None:
                waited_for_stamina = False
                if has_stamina:
                    if self.controller.in_screen(ASSETS.RefillStamina, screenshot=self.controller.get_last_screenshot()):
                        # wait for 10 minutes for stamina to refill
                        logger.warning("Stamina is empty")
                        if wait_for_stamina_to_refill:
                            logger.info("Waiting for stamina to refill")
                            for _ in range(10):
                                self.controller.pause(60)
                                self.controller.take_screenshot()
                            self.controller.click_back()
                            waited_for_stamina = True
                        else:
                            return False
                if not waited_for_stamina:
                    losses += 1
                    if losses >= max_losses:
                        logger.info("Reached max losses")
                        break
            else:
                nodes += 1
                losses = 0
        return True
