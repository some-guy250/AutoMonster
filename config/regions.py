# =============================================================================
# Region definitions for template matching regions
# =============================================================================

from utils.assets import ASSETS


class Region:
    ALL = 0
    TOP = 1
    BOTTOM = 2
    LEFT = 4
    RIGHT = 8
    AD_AREA = 16

    # Combinations
    TOP_LEFT = TOP | LEFT
    TOP_RIGHT = TOP | RIGHT
    BOTTOM_LEFT = BOTTOM | LEFT
    BOTTOM_RIGHT = BOTTOM | RIGHT


AD_REGION = Region.AD_AREA

# Region definitions for each asset
ASSET_REGIONS = {
    ASSETS.Cancel: Region.TOP_RIGHT,
    ASSETS.Continue: Region.BOTTOM,
    ASSETS.ActivityHub: Region.TOP,
    ASSETS.Battles: Region.BOTTOM_LEFT,
    ASSETS.RightArrow: Region.RIGHT,
    ASSETS.EnterBattleRankUp: Region.BOTTOM,
    ASSETS.StartBattleRankUp: Region.BOTTOM_RIGHT,
    ASSETS.AutoBattle: Region.TOP_LEFT,
    ASSETS.Change: Region.BOTTOM,
    ASSETS.ClaimSpin: Region.BOTTOM_RIGHT,
    ASSETS.StartBattle: Region.BOTTOM_RIGHT,
    ASSETS.Wheel: Region.TOP_RIGHT,
    ASSETS.SpinWheel: Region.BOTTOM_RIGHT,
    ASSETS.EnterCavern: Region.BOTTOM,
    ASSETS.ResourceDungeon: Region.BOTTOM,
    ASSETS.EnterBattleStamina: Region.BOTTOM,
    ASSETS.Slider: Region.BOTTOM,
    ASSETS.Slider2: Region.BOTTOM,
    ASSETS.PlayCutscene: Region.BOTTOM,
    ASSETS.EnterEraSaga: Region.BOTTOM,
    ASSETS.CavernMisery: Region.TOP_LEFT,
    ASSETS.CavernConspiracy: Region.TOP_LEFT,
    ASSETS.CavernFeral: Region.TOP_LEFT,
    ASSETS.CavernHistoria: Region.TOP_LEFT,
    ASSETS.CavernMultiverse: Region.TOP_LEFT,
    ASSETS.CavernEvaris: Region.TOP_LEFT,
    ASSETS.CavernGeneza: Region.TOP_LEFT,
    ASSETS.CavernJestin: Region.TOP_LEFT,
    ASSETS.CavernBaBa: Region.TOP_LEFT,
    ASSETS.CavernKhalorc: Region.TOP_LEFT,
    ASSETS.CavernTyr: Region.TOP_LEFT,
    ASSETS.CavernRobur: Region.TOP_LEFT,
    ASSETS.CavernTheton: Region.TOP_LEFT,
    ASSETS.CavernGriffania: Region.TOP_LEFT,
    ASSETS.CavernAlpine: Region.TOP_LEFT,
    ASSETS.CavernAbyssal: Region.TOP_LEFT,
    ASSETS.CavernGalactic: Region.TOP_LEFT,
    ASSETS.CavernBlossom: Region.TOP_LEFT,
    ASSETS.CavernDoomed: Region.TOP_LEFT,
    ASSETS.CavernMetro: Region.TOP_LEFT,
    ASSETS.CavernCorrupted: Region.TOP_LEFT,
    ASSETS.CavernCosmic: Region.TOP_LEFT,
    ASSETS.CavernOriginal: Region.TOP_LEFT,
    ASSETS.PlayVideo: Region.BOTTOM,
    ASSETS.CollectAd: Region.BOTTOM_LEFT,
    ASSETS.Exit: Region.BOTTOM_RIGHT,
    ASSETS.SelectTeam: Region.BOTTOM_LEFT,
    ASSETS.StartBattleGray: Region.BOTTOM_RIGHT,
    ASSETS.RankUp1: Region.LEFT,
    ASSETS.RankUp2: Region.LEFT,
    ASSETS.RankUp3: Region.LEFT,
    ASSETS.RankUp4: Region.LEFT,
    ASSETS.RankUp5: Region.LEFT,
    ASSETS.RankUp6: Region.LEFT,
    ASSETS.RankUp1Synergy: Region.LEFT,
    ASSETS.RankUp2Synergy: Region.LEFT,
    ASSETS.RankUp3Synergy: Region.LEFT,
    ASSETS.RankUp4Synergy: Region.LEFT,
    ASSETS.RankUp5Synergy: Region.LEFT,
    ASSETS.RankUp6Synergy: Region.LEFT,
    ASSETS.RankUpSelected1: Region.LEFT,
    ASSETS.RankUpSelected2: Region.LEFT,
    ASSETS.RankUpSelected3: Region.LEFT,
    ASSETS.RankUpSelected4: Region.LEFT,
    ASSETS.RankUpSelected5: Region.LEFT,
    ASSETS.RankUpSelected6: Region.LEFT,
    ASSETS.Selected1: Region.TOP,
    ASSETS.Selected2: Region.TOP,
    ASSETS.Selected3: Region.TOP,
    ASSETS.Cavern: Region.RIGHT,
    ASSETS.ChangeTeam: Region.BOTTOM_LEFT,
    ASSETS.BackPVP: Region.TOP_LEFT,
    ASSETS.Back: Region.TOP_LEFT,
    ASSETS.NotFullTeam: Region.BOTTOM,
    ASSETS.FlashRaid: Region.TOP,

    ASSETS.BoxSpeedup: Region.BOTTOM,
    ASSETS.CollectPVP: Region.BOTTOM,
    ASSETS.StartBattlePVP: Region.BOTTOM,
    ASSETS.EnterBattlePVP: Region.BOTTOM_RIGHT,
    ASSETS.BoxDone: Region.BOTTOM,
    ASSETS.EnterMultiplayer: Region.BOTTOM,
    ASSETS.ReduceTime: Region.BOTTOM,
    ASSETS.ReduceTimeGold: Region.BOTTOM,
    ASSETS.NextPVP: Region.BOTTOM_RIGHT,

    ASSETS.HavingFun: Region.TOP,
    ASSETS.No: Region.BOTTOM_LEFT,
    ASSETS.DiscardPVP: Region.BOTTOM_RIGHT,
    ASSETS.PVPNoPoints: Region.BOTTOM_RIGHT,

    ASSETS.Rarity: Region.BOTTOM_LEFT,
    ASSETS.RarityRSelected: Region.BOTTOM,
    ASSETS.RarityUCSelected: Region.BOTTOM,
    ASSETS.ElementFireSelected: Region.BOTTOM,
    ASSETS.Element: Region.BOTTOM_RIGHT,
    ASSETS.ElementFire: Region.BOTTOM_RIGHT,
    ASSETS.MonsterUC: Region.ALL,
    ASSETS.MonsterR: Region.ALL,
    ASSETS.RarityUC: Region.BOTTOM_LEFT,
    ASSETS.RarityR: Region.BOTTOM_LEFT,
    ASSETS.StartUnlocking: Region.BOTTOM_LEFT,
    ASSETS.BoxToUnlock: Region.BOTTOM,
    ASSETS.Feed: Region.BOTTOM_LEFT,
    ASSETS.MonsterInfo: Region.TOP,
    ASSETS.Sell: Region.BOTTOM_RIGHT,
    ASSETS.SellOwned: Region.BOTTOM_RIGHT,
    ASSETS.Yes: Region.BOTTOM_RIGHT,
    ASSETS.MonsterEmpty: Region.ALL,
    ASSETS.Unlock: Region.ALL,
    ASSETS.Repeat: Region.BOTTOM_RIGHT,
    ASSETS.TakeEgg: Region.BOTTOM,
    ASSETS.Place: Region.BOTTOM_LEFT,
    ASSETS.Tree: Region.ALL,
    ASSETS.Mountain: Region.ALL,
    ASSETS.FullHatchery: Region.TOP_RIGHT,
    ASSETS.Hatchery: Region.ALL,
    ASSETS.HatchDino: Region.BOTTOM,
    ASSETS.HatchPanda: Region.BOTTOM,
    ASSETS.PlaceVault: Region.ALL,
    ASSETS.HatchNotYet: Region.TOP_RIGHT,

    ASSETS.ClaimDaily: Region.BOTTOM,
    ASSETS.RuneLevel: Region.BOTTOM_LEFT,
    ASSETS.RuneType: Region.BOTTOM_RIGHT,
    ASSETS.RuneCraft: Region.BOTTOM,
    ASSETS.RuneLevel1: Region.BOTTOM_LEFT,
    ASSETS.RuneLevel2: Region.BOTTOM_LEFT,
    ASSETS.RuneLevel3: Region.BOTTOM_LEFT,
    ASSETS.RuneLevel4: Region.BOTTOM_LEFT,
    ASSETS.RuneLevel5: Region.BOTTOM_LEFT,
    ASSETS.RuneLife: Region.BOTTOM_RIGHT,
    ASSETS.RuneStrength: Region.BOTTOM_RIGHT,
    ASSETS.RuneStamina: Region.BOTTOM_RIGHT,
    ASSETS.RuneSpeed: Region.BOTTOM_RIGHT,
    ASSETS.RuneGold: Region.BOTTOM_RIGHT,

    ASSETS.RuneCollect: Region.BOTTOM_RIGHT,

    ASSETS.RuneDrop: Region.ALL,
}
