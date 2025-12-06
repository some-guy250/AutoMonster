import cv2
import numpy as np
import pathlib
from typing import List, Optional, Tuple
import logging

from Constants import ASSETS, ASSET_REGIONS, Region, ADS_DIR, AD_REGION
from utils.logger import setup_logger

logger = setup_logger()

class VisionManager:
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.template_dict = {}
        self.asset_reverse_map = {v: k for k, v in ASSETS.__dict__.items() if not k.startswith('__')}
        self.region_reverse_map = {v: k for k, v in Region.__dict__.items() if not k.startswith('__')}
        self.load_templates()

    def load_templates(self):
        """Reload all templates from disk and Constants.py"""
        self.template_dict = {}
        self.ad_keys = []
        pathlib.Path('assets').mkdir(parents=True, exist_ok=True)
        
        for asset in dir(ASSETS):
            if asset.startswith('__'):
                continue
            png_file = getattr(ASSETS, asset)

            if png_file not in ASSET_REGIONS:
                logger.debug(f"Asset '{png_file}' (ASSETS.{asset}) has no region defined. Defaulting to Region.ALL")
            elif ASSET_REGIONS[png_file] == Region.ALL:
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

    def get_cords(self, asset_code: str, screenshot: np.ndarray, threshold: float = .9, gray_img: bool = False) -> List[List[int]]:
        if asset_code not in self.template_dict:
            logger.error(f"Asset {asset_code} not found in templates")
            return []

        template, h, w = self.template_dict[asset_code]

        # Determine region and crop
        region = ASSET_REGIONS.get(asset_code, Region.ALL)
        if asset_code.startswith(f"{ADS_DIR}/"):
            region = AD_REGION
        sh, sw = screenshot.shape[:2]
        
        # Calculate crop boundaries
        y_start, y_end = 0, sh
        x_start, x_end = 0, sw
        
        if region == Region.AD_AREA:
            # Special region for ads: Top-Left (1/9) and Top-Right (1/9)
            # We'll search in two separate crops and combine results
            
            # Top 1/3 height
            y_end = sh // 3
            
            # Left 1/3 width
            x_end_left = sw // 3
            
            # Right 1/3 width
            x_start_right = (sw * 2) // 3
            
            crops = [
                (screenshot[0:y_end, 0:x_end_left], 0, 0),  # Top-Left
                (screenshot[0:y_end, x_start_right:sw], x_start_right, 0)  # Top-Right
            ]
            
            final_locations = []
            
            for img_crop, crop_x, crop_y in crops:
                if gray_img:
                    img_crop = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
                    # Template conversion happens once outside loop if needed, but here we do it per crop if not done
                    # Actually template is already converted if gray_img is True? No, let's check below.
                
                # Prepare template
                curr_template = template
                if gray_img and len(curr_template.shape) == 3:
                    curr_template = cv2.cvtColor(curr_template, cv2.COLOR_BGR2GRAY)
                
                res = cv2.matchTemplate(img_crop, curr_template, cv2.TM_CCOEFF_NORMED)
                locs = np.where(res >= threshold)
                
                # Adjust coordinates back to full image
                for i in range(len(locs[0])):
                    final_locations.append((locs[0][i] + crop_y, locs[1][i] + crop_x))
            
            # Group locations (copied from below)
            location_groups = []
            for loc in final_locations:
                if len(location_groups) == 0:
                    location_groups.append([loc])
                else:
                    for group in location_groups:
                        if abs(group[-1][0] - loc[0]) < 5 and abs(group[-1][1] - loc[1]) < 5:
                            group.append(loc)
                            break
                    else:
                        location_groups.append([loc])

            # update location to be the center of the group
            result_locations = []
            for group in location_groups:
                x = sum(loc[1] for loc in group) // len(group)
                y = sum(loc[0] for loc in group) // len(group)
                # Add half width/height to get center of match
                result_locations.append([x + w // 2, y + h // 2])
                
            return result_locations

        if region & Region.TOP:
            y_end = sh // 2
        elif region & Region.BOTTOM:
            y_start = sh // 2
            
        if region & Region.LEFT:
            x_end = sw // 2
        elif region & Region.RIGHT:
            x_start = sw // 2
            
        # Apply crop
        img_to_match = screenshot[y_start:y_end, x_start:x_end]
        crop_x, crop_y = x_start, y_start

        if gray_img:
            img_to_match = cv2.cvtColor(img_to_match, cv2.COLOR_BGR2GRAY)
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        res = cv2.matchTemplate(img_to_match, template, cv2.TM_CCOEFF_NORMED)

        location = np.where(res >= threshold)

        location = [(location[0][i], location[1][i]) for i in range(len(location[0]))]

        # group the locations that are close to each other by 5px in each direction
        location_groups = []
        for loc in location:
            if len(location_groups) == 0:
                location_groups.append([loc])
            else:
                for group in location_groups:
                    if abs(group[-1][0] - loc[0]) < 5 and abs(group[-1][1] - loc[1]) < 5:
                        group.append(loc)
                        break
                else:
                    location_groups.append([loc])

        # update location to be the center of the group
        final_locations = []
        for group in location_groups:
            x = sum(loc[1] for loc in group) // len(group)
            y = sum(loc[0] for loc in group) // len(group)
            
            # Adjust coordinates back to full screen
            x += crop_x
            y += crop_y

            # Suggest region optimization if currently using ALL
            if region == Region.ALL:
                r = 0
                # Vertical check
                if y + h <= sh // 2:
                    r |= Region.TOP
                elif y >= sh // 2:
                    r |= Region.BOTTOM
                
                # Horizontal check
                if x + w <= sw // 2:
                    r |= Region.LEFT
                elif x >= sw // 2:
                    r |= Region.RIGHT
                
                if r != 0:
                    # Try to find exact match in Region constants first
                    region_name = self.region_reverse_map.get(r)
                    
                    if region_name:
                        suggested_str = f"Region.{region_name}"
                    else:
                        # Fallback to composite
                        region_names = []
                        if r & Region.TOP: region_names.append("TOP")
                        if r & Region.BOTTOM: region_names.append("BOTTOM")
                        if r & Region.LEFT: region_names.append("LEFT")
                        if r & Region.RIGHT: region_names.append("RIGHT")
                        suggested_str = " | ".join(["Region." + name for name in region_names])
                    
                    asset_name = self.asset_reverse_map.get(asset_code)
                    if asset_name:
                        logger.info(f"Optimization Suggestion: ASSETS.{asset_name}: {suggested_str},")
                    else:
                        logger.info(f"Optimization Suggestion: Asset '{asset_code}' found in {suggested_str}")

            # add half the width and height of the template to the location and cast to int
            # Use device_manager for scaling
            final_locations.append([self.device_manager.scale_x(int(x + w / 1.9)), self.device_manager.scale_y(int(y + h / 1.9))])
        
        # Sort by x-coordinate (left to right)
        final_locations.sort(key=lambda loc: loc[0])
        
        return final_locations

    def count(self, *assets, screenshot: np.ndarray, gray_img=False, threshold=.9):
        total = 0
        for a in assets:
            total += len(self.get_cords(a, screenshot, gray_img=gray_img, threshold=threshold))
        return total

    def get_template_image(self, asset_code: str) -> Optional[np.ndarray]:
        if asset_code in self.template_dict:
            return self.template_dict[asset_code][0]
        return None
