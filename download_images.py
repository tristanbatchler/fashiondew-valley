from tailoring import tailoring_data
from dyeing import dyeing_info
from pathlib import Path
import requests
import os
from PIL import Image
from tint_images import tint_image

CWD = Path(__file__).parent

def download_images():
    for item in tailoring_data:
        img_path = Path(CWD / "images" / item.type / sanitize_name(item.name) / "original.png")

        # Download the original image
        if not img_path.exists():
            reduce = 3 if item.type == "hat" else 4
            download_image(item.image_url, img_path, reduce_size_by=reduce)
        
        # Get the dyed versions of the image
        for color in dyeing_info:
            for strength in [25, 50, 75, 100]:
                if item.dyeable:
                    tint_image(img_path, color, strength)

    # Download all ingredient images
    ingredients = set()
    for item in tailoring_data:
        for ingredient in item.ingredients:
            ingredients.add(ingredient)

    for ingredient in ingredients:
        img_path = Path(CWD / "images" / "ingredients" / (sanitize_name(ingredient.name) + ".png"))
        if not img_path.exists():
            # print(f"Downloading {ingredient.name}")
            download_image(ingredient.image_url, img_path)
        else:
            print(f"Skipping {ingredient.name} (already downloaded)")

    # Download the rest of the ingredient images (from dyeing.py)
    for color in dyeing_info:
        for ingredient in dyeing_info[color]["ingredients"]:
            img_path = Path(CWD / "images" / "ingredients" / (sanitize_name(ingredient.name) + ".png"))
            if not img_path.exists():
                # print(f"Downloading {ingredient.name}")
                download_image(ingredient.image_url, img_path)
            else:
                print(f"Skipping {ingredient.name} (already downloaded)")


def download_image(url, output_path, reduce_size_by=1):
    os.makedirs(output_path.parent, exist_ok=True)
    response = requests.get(url)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    #Resize to 8x8 (nearest neighbor) as many of these are upscaled to either 32x32, 48x48, or 54x54
    # This is to make the images actually pixel perfect as they are in the game
    if reduce_size_by > 1:
        img = Image.open(output_path)
        img = img.resize((img.width // reduce_size_by, img.height // reduce_size_by), Image.NEAREST)
        img.save(output_path)

def sanitize_name(name):
    return "".join(x for x in name if x.isalnum())
