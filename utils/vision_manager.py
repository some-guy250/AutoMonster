import pathlib

import cv2
import numpy as np

from utils.assets import ASSETS, ADS_DIR
from config.regions import AD_REGION, Region
from config.config import DEFAULT_TEMPLATE_THRESHOLD, RUNE_THRESHOLD
from utils.asset_registry import ASSET_SPECS, get_spec, RUNE_PREFIXES
from utils.logger import setup_logger
from utils.region_utils import recommend_region

logger = setup_logger()

# Divisor used to offset a match's top-left corner to the point we click.
# ~1/2 lands on the template centre; 1.9 nudges slightly towards the right of
# centre, which is where the game's clickable buttons sit. Kept in one place so
# both the ad and normal branches click the same relative spot.
CLICK_CENTER_DIVISOR = 1.9


def group_nearby(points, gap: int = 5):
    """Group (y, x) match points that are within ``gap`` px of each other.

    Returns the centroid (x, y) of each group. A point joins the first group
    whose *most recent* point is close enough, matching the previous
    behaviour exactly.
    """
    groups = []
    for loc in points:
        for group in groups:
            if abs(group[-1][0] - loc[0]) < gap and abs(group[-1][1] - loc[1]) < gap:
                group.append(loc)
                break
        else:
            groups.append([loc])

    centroids = []
    for group in groups:
        y = sum(p[0] for p in group) // len(group)
        x = sum(p[1] for p in group) // len(group)
        centroids.append((x, y))
    return centroids


class VisionManager:
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.template_dict = {}
        self.asset_reverse_map = {v: k for k, v in ASSETS.__dict__.items() if not k.startswith('_')}
        self.load_templates()

    def load_templates(self):
        """Reload all templates from disk and the AssetSpec registry."""
        self.template_dict = {}
        self.ad_keys = []
        for asset in dir(ASSETS):
            if asset.startswith('__'):
                continue
            png_file = getattr(ASSETS, asset)

            spec = get_spec(png_file)
            if spec.region == Region.ALL:
                logger.debug(f"Asset '{png_file}' (ASSETS.{asset}) is using Region.ALL. Consider optimizing.")

            if pathlib.Path(f'assets/{png_file}').exists():
                img = cv2.imread(f'assets/{png_file}')
                if img is None:
                    logger.warning(f"Failed to load image: assets/{png_file}")
                    continue
                self.template_dict[png_file] = (img, img.shape[0], img.shape[1])
            else:
                logger.warning(f'Asset {png_file} is missing')

        # Load ads
        ads_path = pathlib.Path('assets') / ADS_DIR
        if ads_path.exists():
            for file in ads_path.glob('*.png'):
                key = f"{ADS_DIR}/{file.name}"
                img = cv2.imread(str(file))
                if img is not None:
                    self.template_dict[key] = (img, img.shape[0], img.shape[1])
                    self.ad_keys.append(key)

        # Load dynamic rune variants (rune{level}{type}{s/t}.png) captured on disk.
        assets_path = pathlib.Path('assets')
        for file in assets_path.glob('rune*.png'):
            if file.name.startswith(RUNE_PREFIXES):
                img = cv2.imread(str(file))
                if img is not None:
                    self.template_dict[file.name] = (img, img.shape[0], img.shape[1])

    def _resolve(self, asset_code: str, threshold: float, gray_img: bool) -> tuple:
        """Apply per-asset threshold/gray overrides from the AssetSpec registry.

        Mirrors the previous Controller._get_cords resolution exactly:
        - an explicit per-asset threshold (slider, cavern, ...) always wins;
        - a dynamic rune variant uses the strict rune threshold only when the
          caller kept the default;
        - an asset flagged gray always matches in grayscale.
        """
        spec = get_spec(asset_code)
        if spec.threshold != DEFAULT_TEMPLATE_THRESHOLD:
            threshold = spec.threshold
        elif threshold == DEFAULT_TEMPLATE_THRESHOLD and asset_code.startswith(RUNE_PREFIXES):
            threshold = RUNE_THRESHOLD
        if spec.gray:
            gray_img = True
        return threshold, gray_img

    def get_cords(self, asset_code: str, screenshot: np.ndarray, threshold: float = DEFAULT_TEMPLATE_THRESHOLD, gray_img: bool = False):
        if asset_code not in self.template_dict:
            logger.error(f"Asset {asset_code} not found in templates")
            return []

        template, h, w = self.template_dict[asset_code]
        threshold, gray_img = self._resolve(asset_code, threshold, gray_img)

        region = get_spec(asset_code).region
        if asset_code.startswith(f"{ADS_DIR}/"):
            region = AD_REGION
        sh, sw = screenshot.shape[:2]

        if region == Region.AD_AREA:
            return self._match_ad_area(template, screenshot, threshold, gray_img, w, h)

        # Crop to the recommended region to cut matching cost.
        y_start, y_end = 0, sh
        x_start, x_end = 0, sw
        if region & Region.TOP:
            y_end = sh // 2
        elif region & Region.BOTTOM:
            y_start = sh // 2
        if region & Region.LEFT:
            x_end = sw // 2
        elif region & Region.RIGHT:
            x_start = sw // 2

        img_to_match = screenshot[y_start:y_end, x_start:x_end]

        if gray_img:
            img_to_match = cv2.cvtColor(img_to_match, cv2.COLOR_BGR2GRAY)
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(img_to_match, template, cv2.TM_CCOEFF_NORMED)
        location = np.where(res >= threshold)
        points = [(location[0][i], location[1][i]) for i in range(len(location[0]))]

        final_locations = []
        for x, y in group_nearby(points):
            # Adjust back to full screen coordinates.
            x += x_start
            y += y_start

            # Suggest region optimization only for assets with no explicit spec.
            if asset_code not in ASSET_SPECS:
                suggested_str = recommend_region(x, y, w, h)
                asset_name = self.asset_reverse_map.get(asset_code)
                if asset_name:
                    logger.debug(f"Optimization Suggestion: ASSETS.{asset_name}: {suggested_str},")
                else:
                    logger.debug(f"Optimization Suggestion: Asset '{asset_code}' found in {suggested_str}")

            final_locations.append([
                self.device_manager.scale_x(int(x + w / CLICK_CENTER_DIVISOR)),
                self.device_manager.scale_y(int(y + h / CLICK_CENTER_DIVISOR)),
            ])

        final_locations.sort(key=lambda loc: loc[0])
        return final_locations

    def _match_ad_area(self, template, screenshot, threshold, gray_img, w, h):
        """Match in the two top corners where ad close buttons live."""
        sh, sw = screenshot.shape[:2]
        y_end = sh // 3
        x_end_left = sw // 3
        x_start_right = (sw * 2) // 3

        crops = [
            (screenshot[0:y_end, 0:x_end_left], 0, 0),
            (screenshot[0:y_end, x_start_right:sw], x_start_right, 0),
        ]

        all_points = []
        for img_crop, crop_x, crop_y in crops:
            curr_template = template
            if gray_img:
                img_crop = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
                if len(curr_template.shape) == 3:
                    curr_template = cv2.cvtColor(curr_template, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(img_crop, curr_template, cv2.TM_CCOEFF_NORMED)
            locs = np.where(res >= threshold)
            for i in range(len(locs[0])):
                all_points.append((locs[0][i] + crop_y, locs[1][i] + crop_x))

        dm = self.device_manager
        result_locations = []
        for x, y in group_nearby(all_points):
            result_locations.append([
                dm.scale_x(int(x + w / CLICK_CENTER_DIVISOR)),
                dm.scale_y(int(y + h / CLICK_CENTER_DIVISOR)),
            ])
        result_locations.sort(key=lambda loc: loc[0])
        return result_locations

    def count(self, *assets, screenshot: np.ndarray, gray_img=False, threshold=DEFAULT_TEMPLATE_THRESHOLD):
        total = 0
        for a in assets:
            total += len(self.get_cords(a, screenshot, gray_img=gray_img, threshold=threshold))
        return total

    def get_template_image(self, asset_code: str) -> np.ndarray | None:
        if asset_code in self.template_dict:
            return self.template_dict[asset_code][0]
        return None
