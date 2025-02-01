import os
import time
import cv2
import requests
from PIL import Image
from tqdm import tqdm

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


def download_assets():
    # Send a GET request to the GitHub API to retrieve information about the contents of the "assets" folder
    response = requests.get(f"{repo_url_api}/contents/assets")

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        contents = response.json()

        # Create the "assets" folder if it doesn't exist
        assets_folder = "assets"
        if not os.path.exists(assets_folder):
            os.makedirs(assets_folder)

        # Iterate through each item in the contents
        for item in tqdm(contents, desc="Downloading assets", unit="file", dynamic_ncols=True):
            # Check if the item is a file
            if item["type"] == "file":
                # Get the download URL for the file
                download_url = item["download_url"]

                # Extract the file name from the URL
                file_name = os.path.basename(download_url)

                # Define the file path to save the file
                file_path = os.path.join(assets_folder, file_name)

                # Send a GET request to download the file
                response = requests.get(download_url)

                # Save the file
                with open(file_path, "wb") as f:
                    f.write(response.content)
    else:
        print(f"Failed to retrieve contents. Status code: {response.status_code}")


def crush_png(image_path):
    # Open an existing image
    image = Image.open(image_path)
    image.save(image_path)


def crush_assets():
    for file in tqdm(os.listdir("assets"), desc="Crushing assets", unit="file", dynamic_ncols=True):
        if file.endswith(".png"):
            crush_png(f"assets/{file}")

# crush_assets()
