import os
import time
import cv2
from PIL import Image

repo_url_api = "https://api.github.com/repos/some-guy250/AutoMonster"
repo_url = "https://github.com/some-guy250/AutoMonster"


def time_function(func, *args, **kwargs) -> any:
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    delta = end - start
    # make it to a h m s format or m s format or s format depending on the time
    if delta > 3600:
        delta = f"{delta // 3600}h {delta % 3600 // 60}m {delta % 60:.2f}s"
    elif delta > 60:
        delta = f"{delta // 60}m {delta % 60:.2f}s"
    else:
        delta = f"{delta:.2f}s"
    print(f"Time taken for {func.__name__} is {delta}, result is {result}")
    return result


def compare_imgs(img1, img2, transform_to_black=False):
    if img1.shape == img2.shape:
        height, width, _ = img2.shape
        if transform_to_black:
            img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        errorL2 = cv2.norm(img1, img2, cv2.NORM_L2)
        similarity = 1 - errorL2 / (height * width)
        return similarity > 0.99
    return False


def crush_png(image_path):
    # Open an existing image
    image = Image.open(image_path)
    image.save(image_path)


def crush_assets():
    import pathlib
    
    # Crush images in assets root
    for file in os.listdir("assets"):
        if file.endswith(".png"):
            crush_png(f"assets/{file}")
    
    # Crush images in ads subdirectory
    ads_dir = pathlib.Path("assets/ads")
    if ads_dir.exists():
        for file in ads_dir.glob("*.png"):
            crush_png(str(file))
    
    print("Crushed all assets")

# crush_assets()
