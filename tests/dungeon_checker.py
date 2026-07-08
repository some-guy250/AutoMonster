#!/usr/bin/env python3
# =============================================================================
# Dungeon Checker - Test Script
# =============================================================================
# Navigates to the caverns screen and checks which cavern assets are visible.
# Reports a summary of found vs. missing caverns.
#
# Usage: python tests/dungeon_checker.py
# (Run from project root, with venv activated)
# =============================================================================

import sys
import pathlib

# Ensure project root is on sys.path so relative imports work
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from AutoMonster import Controller
from utils.assets import ASSETS, CAVERN_TO_ASSETS
from config.config import CAVERN_THRESHOLD
from utils.logger import setup_logger

logger = setup_logger("DungeonChecker")


def run_dungeon_checker(controller: Controller) -> dict:
    """Navigate through caverns, screenshot each page, and check all cavern assets.

    Returns:
        dict with keys:
            - 'found': dict of cavern_name -> True/False for each cavern
            - 'total_expected': total number of cavern assets to check
    """
    # ── Navigate to caverns ──────────────────────────────────────────────
    logger.info("Navigating to caverns...")
    controller.navigator.goto_cavern()
    controller.pause(2)

    # ── Check caverns page by page, clicking RightArrow between pages ────
    all_cavern_names = list(CAVERN_TO_ASSETS.keys())
    unknown: dict[str, str] = {name: CAVERN_TO_ASSETS[name] for name in all_cavern_names}
    found: dict[str, bool] = {}
    page = 0

    while True:
        page += 1
        logger.info(f"--- Page {page} ---")

        # ── Take screenshot and check only unknown caverns ─────────────────
        screenshot = controller.take_screenshot()

        for cavern_name, asset_code in unknown.items():
            cords = controller._get_cords(asset_code, screenshot, threshold=CAVERN_THRESHOLD)
            if len(cords) > 0:
                found[cavern_name] = True
                logger.info(f"  FOUND: {cavern_name}")
                break  # Each page shows one new cavern — stop checking
            # else: skip, will be added back to unknown below

        unknown = {n: a for n, a in unknown.items() if n not in found}

        # If all caverns found, no need to keep scrolling
        if not unknown:
            logger.info("All caverns found — stopping")
            break

        # ── Click RightArrow to go to next page ────────────────────────────
        if not controller.click(ASSETS.RightArrow, pause=4):
            logger.info("No more RightArrow — reached the end")
            break

    # ── Print summary ────────────────────────────────────────────────────
    total_expected = len(all_cavern_names)
    print("\n" + "=" * 60)
    print("  DUNGEON CHECKER - Results")
    print("=" * 60)
    print(f"  Pages scanned:        {page}")
    print(f"  Total cavern assets:  {total_expected}")
    print(f"  Found (visible):      {len(found)}")
    print(f"  Not seen:             {len(unknown)}")
    print("-" * 60)

    print("\n  [OK] Visible caverns:")
    for name in sorted(found):
        print(f"    - {name}")

    print("\n  [??] Not seen:")
    for name in sorted(unknown):
        print(f"    - {name}")

    print("\n" + "=" * 60 + "\n")

    return {"found": found, "unknown": unknown, "total_expected": total_expected}


def main() -> None:
    logger.info("Starting Dungeon Checker test...")

    # Create controller (connects to device, launches game)
    controller = Controller()

    try:
        result = run_dungeon_checker(controller)

        unknown = result["unknown"]
        if unknown:
            logger.warning(
                f"Dungeon check incomplete: {len(unknown)} cavern(s) not detected: {list(unknown.keys())}"
            )
        else:
            logger.info("All cavern assets detected successfully!")

    except Exception as e:
        logger.error(f"Dungeon checker failed: {e}")


if __name__ == "__main__":
    main()
