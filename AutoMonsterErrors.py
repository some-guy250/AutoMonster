class ExecutionFlag(Exception):
    pass


class AutoMonsterError(Exception):
    pass


class DeviceError(AutoMonsterError):
    pass


class OpenGameError(AutoMonsterError):
    pass


class CloseGameError(AutoMonsterError):
    pass


class ScreenShotError(AutoMonsterError):
    pass


class WaitError(AutoMonsterError):
    pass


class FollowSequenceError(AutoMonsterError):
    pass


class ClickError(AutoMonsterError):
    pass


class GoToError(AutoMonsterError):
    pass


class BattleError(AutoMonsterError):
    pass


class InvalidTeamError(AutoMonsterError):
    pass


class PVPError(AutoMonsterError):
    pass


class InputError(AutoMonsterError):
    pass


class PlayAdsError(AutoMonsterError):
    pass


class SkipAdError(AutoMonsterError):
    pass


class ConnectError(AutoMonsterError):
    pass

class SliderError(AutoMonsterError):
    pass