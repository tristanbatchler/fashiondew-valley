from bs4 import BeautifulSoup
import requests
from items import IngredientItem

# {
#     "red": {
#         "rgb": (220, 0, 0),
#         "ingredients": {
#             IngredientItem(name="Cranberries", image_url="https://stardewvalleywiki.com/mediawiki/images/4/4b/Cranberries.png"): 100,
#             IngredientItem(name="Hot Pepper", image_url="https://stardewvalleywiki.com/mediawiki/images/5/5b/Hot_Pepper.png"): 50,
#             ...
#         }
#     }
# }


def _get_dyeing_info():
    colors = {}

    base = "https://stardewvalleywiki.com/"
    url = base + "Dyeing"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable"})

    table = [table for table in tables if "sortable" in table.get("class")][0]
    rows = table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all("td")
        
        # Ingredient icon, Ingredient name, Color name, RGB value, Dye strength
        ingredient_image = cells[0].find("img")
        if ingredient_image:
            ingredient_image_url = base + ingredient_image.get("src")
        
        ingredient_name = cells[1].text.strip()

        color_name = cells[2].text.strip()
        rgb = tuple(map(int, cells[3].text.strip().split(",")))
        dye_strength_str = cells[4].text.strip().lower()
        dye_strength = 25
        if "strong" in dye_strength_str:
            dye_strength = 100
        elif "medium" in dye_strength_str:
            dye_strength = 50

        ingredient_item = IngredientItem(name=ingredient_name, image_url=ingredient_image_url)
        if color_name not in colors:
            colors[color_name] = {
                "rgb": rgb,
                "ingredients": {}
            }
        colors[color_name]["ingredients"][ingredient_item] = dye_strength


    return colors


dyeing_info = _get_dyeing_info()


def get_required_ingredients_for(color: str, strength: int) -> list[IngredientItem]:
    color_info = dyeing_info.get(color)
    if not color_info:
        return []

    ingredients = color_info["ingredients"]
    return [ingredient for ingredient, dye_strength in ingredients.items() if dye_strength == strength]

if __name__ == '__main__':
    print()
    for ingredient in get_required_ingredients_for("red", 100):
        print(ingredient.name)