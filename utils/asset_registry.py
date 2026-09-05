# =============================================================================
# Single source of truth for per-asset template-matching metadata.
#
# Merged from the former ASSET_REGIONS (config/regions.py), ASSET_THRESHOLDS
# and ASSET_GRAY_IMG (config/config.py). Add a new asset by adding one entry
# here. Omitted fields fall back to the defaults in AssetSpec.
# =============================================================================

from dataclasses import dataclass

from config.regions import Region
from config.config import (
    DEFAULT_TEMPLATE_THRESHOLD,
    SLIDER_THRESHOLD,
    CAVERN_THRESHOLD,
)


@dataclass(frozen=True)
class AssetSpec:
    """Per-asset matching metadata."""

    region: int = Region.ALL
    threshold: float = DEFAULT_TEMPLATE_THRESHOLD
    gray: bool = False


ASSET_SPECS = {
    'cancel.png': AssetSpec(region=Region.TOP | Region.RIGHT, threshold=0.8),
    'continue.png': AssetSpec(region=Region.BOTTOM),
    'acthub.png': AssetSpec(region=Region.TOP),
    'battles.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'rightharrow.png': AssetSpec(region=Region.RIGHT),
    'enterbattlerankup.png': AssetSpec(region=Region.BOTTOM),
    'startbattlerankup.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'auto.png': AssetSpec(region=Region.TOP | Region.LEFT),
    'change.png': AssetSpec(region=Region.BOTTOM),
    'claimspin.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'fight.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'wheel.png': AssetSpec(region=Region.TOP | Region.RIGHT),
    'spinwheel.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT, gray=True),
    'entercavern.png': AssetSpec(region=Region.BOTTOM),
    'resourcedungeon.png': AssetSpec(region=Region.BOTTOM),
    'stamina.png': AssetSpec(region=Region.BOTTOM),
    'slider.png': AssetSpec(region=Region.BOTTOM, threshold=SLIDER_THRESHOLD),
    'slider2.png': AssetSpec(region=Region.BOTTOM, threshold=SLIDER_THRESHOLD),
    'playcut.png': AssetSpec(region=Region.BOTTOM),
    'entersaga.png': AssetSpec(region=Region.BOTTOM),
    'cavernmisery.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernconspiracy.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernferal.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernhistoria.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernmultiverse.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernevaris.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverngeneza.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernjestin.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernbaba.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernkhalorc.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverntyr.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernrobur.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverntheton.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverngriffania.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernalpine.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernabyssal.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverngalactic.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernblossom.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverndoomed.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernmetro.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverncorrupted.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'caverncosmic.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'cavernoriginal.png': AssetSpec(region=Region.TOP | Region.LEFT, threshold=CAVERN_THRESHOLD, gray=True),
    'playvideo.png': AssetSpec(region=Region.BOTTOM),
    'collectad.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'exit.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'selectteam.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'fightgray.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'rankup1.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup2.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup3.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup4.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup5.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup6.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup1s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup2s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup3s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup4s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup5s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankup6s.png': AssetSpec(region=Region.LEFT, gray=True),
    'rankups1.png': AssetSpec(region=Region.LEFT),
    'rankups2.png': AssetSpec(region=Region.LEFT),
    'rankups3.png': AssetSpec(region=Region.LEFT),
    'rankups4.png': AssetSpec(region=Region.LEFT),
    'rankups5.png': AssetSpec(region=Region.LEFT),
    'rankups6.png': AssetSpec(region=Region.LEFT),
    'selected1.png': AssetSpec(region=Region.TOP),
    'selected2.png': AssetSpec(region=Region.TOP),
    'selected3.png': AssetSpec(region=Region.TOP),
    'cavern.png': AssetSpec(region=Region.TOP),
    'changeteam.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'backpvp.png': AssetSpec(region=Region.TOP | Region.LEFT),
    'back.png': AssetSpec(region=Region.TOP | Region.LEFT),
    'notfullteam.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'flashraid.png': AssetSpec(region=Region.TOP),
    'noundefeated.png': AssetSpec(region=Region.TOP | Region.LEFT),
    'quitgame.png': AssetSpec(region=Region.TOP | Region.LEFT),
    'boxspeedup.png': AssetSpec(region=Region.BOTTOM, gray=True),
    'collectpvp.png': AssetSpec(region=Region.BOTTOM),
    'fightpvp.png': AssetSpec(region=Region.BOTTOM),
    'enterbattlepvp.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'boxdone.png': AssetSpec(region=Region.BOTTOM),
    'entermultiplayer.png': AssetSpec(region=Region.BOTTOM),
    'reducetime.png': AssetSpec(region=Region.BOTTOM),
    'reducetimegold.png': AssetSpec(region=Region.BOTTOM),
    'nextpvp.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'havingfun.png': AssetSpec(region=Region.TOP),
    'no.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'discardpvp.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'pvpnomore.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'rarity.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'rarityrs.png': AssetSpec(region=Region.BOTTOM),
    'rarityucs.png': AssetSpec(region=Region.BOTTOM),
    'elementfires.png': AssetSpec(region=Region.BOTTOM),
    'element.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'elementfire.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'monsteruc.png': AssetSpec(region=Region.ALL),
    'monsterr.png': AssetSpec(region=Region.ALL),
    'rarityuc.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'rarityr.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'startunlocking.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'boxtounlock.png': AssetSpec(region=Region.BOTTOM, gray=True),
    'feed.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'monsterinfo.png': AssetSpec(region=Region.TOP),
    'sell.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT, threshold=0.8),
    'sellowned.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'yes.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT, threshold=0.8),
    'monsterempty.png': AssetSpec(region=Region.ALL),
    'unlock.png': AssetSpec(region=Region.ALL),
    'repeat.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT, threshold=0.8),
    'takeegg.png': AssetSpec(region=Region.BOTTOM, threshold=0.75),
    'place.png': AssetSpec(region=Region.BOTTOM | Region.LEFT, threshold=0.8),
    'tree.png': AssetSpec(region=Region.ALL, threshold=0.90),
    'mountain.png': AssetSpec(region=Region.ALL, threshold=0.90),
    'fullhatchery.png': AssetSpec(region=Region.TOP | Region.RIGHT, threshold=0.8),
    'hatchery.png': AssetSpec(region=Region.ALL, threshold=0.8),
    'hatchdino.png': AssetSpec(region=Region.BOTTOM, threshold=0.8),
    'hatchpanda.png': AssetSpec(region=Region.BOTTOM, threshold=0.8),
    'placevault.png': AssetSpec(region=Region.ALL, threshold=0.8),
    'hatchnotyet.png': AssetSpec(region=Region.TOP | Region.RIGHT, threshold=0.8),
    'speedup.png': AssetSpec(region=Region.BOTTOM, threshold=0.8),
    'claimdaily.png': AssetSpec(region=Region.BOTTOM),
    'runelevel.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runetype.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runecraft.png': AssetSpec(region=Region.BOTTOM),
    'runelevel1.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runelevel2.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runelevel3.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runelevel4.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runelevel5.png': AssetSpec(region=Region.BOTTOM | Region.LEFT),
    'runelife.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runestrength.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runestamina.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runespeed.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runegold.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runecollect.png': AssetSpec(region=Region.BOTTOM | Region.RIGHT),
    'runedrop.png': AssetSpec(region=Region.ALL),
}


# Dynamic rune variants (rune{level}{type}{s/t}.png) are captured on disk and
# are not listed above. They are small and similar to each other, so they need
# the stricter RUNE_THRESHOLD.
RUNE_PREFIXES = ("rune1", "rune2", "rune3", "rune4", "rune5")


def get_spec(asset_code: str) -> AssetSpec:
    """Return the explicit spec for an asset, or a fully default spec if absent.

    The dynamic-rune threshold fallback is applied by the vision layer (see
    VisionManager.get_cords) so that an explicitly caller-supplied threshold
    is never clobbered.
    """
    return ASSET_SPECS.get(asset_code, AssetSpec())
