import os
import pathlib
import cv2
import logging
from PIL import Image
from config.config import IMAGE_SIMILARITY_THRESHOLD

logger = logging.getLogger(__name__)

repo_url_api = "https://api.github.com/repos/some-guy250/AutoMonster"
repo_url = "https://github.com/some-guy250/AutoMonster"


def compare_imgs(img1, img2, transform_to_black=False):
    """Compare two images for similarity.

    Returns True if the images are >99% similar.
    """
    if img1.shape == img2.shape:
        height, width, _ = img2.shape
        if transform_to_black:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        error_l2 = cv2.norm(img1, img2, cv2.NORM_L2)
        similarity = 1 - error_l2 / (height * width)
        return similarity > IMAGE_SIMILARITY_THRESHOLD
    return False


def crush_png(image_path):
    """Re-save a PNG to strip metadata and reduce file size."""
    image = Image.open(image_path)
    image.save(image_path)


def crush_assets():
    """Crush all PNG assets in asset_images/ and asset_images/ads/."""
    for file in os.listdir("assets"):
        if file.endswith(".png"):
            crush_png(f"asset_images/{file}")

    ads_dir = pathlib.Path("asset_images/ads")
    if ads_dir.exists():
        for file in ads_dir.glob("*.png"):
            crush_png(str(file))

    logger.debug("Crushed all assets")
