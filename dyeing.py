from bs4 import BeautifulSoup
import requests
from items import IngredientItem, IngredientCombination
from dataclasses import dataclass

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



def get_ingredients_choices(desired_color: str, desired_strength: int, favour: list[IngredientItem] | None = None) -> set[IngredientCombination]:
    """The return value represents the choices the user has available. Each choice is an ingredient or combination of ingredients that can be used to achieve the desired color and strength."""
    ingredients_strengths = dyeing_info[desired_color]["ingredients"].items()

    choices = set()
    for ingredient, strength in ingredients_strengths:
        if strength == desired_strength:
            combination = IngredientCombination()
            combination.add(ingredient, strength//25)
            choices.add(combination)
        elif strength < desired_strength:
            desired_strength_2 = desired_strength - strength
            for ingredient_2, strength_2 in ingredients_strengths:
                if strength_2 == desired_strength_2:
                    combination = IngredientCombination()
                    combination.add(ingredient, strength//25)
                    combination.add(ingredient_2, strength_2//25)
                    choices.add(combination)
                elif strength_2 < desired_strength_2:
                    desired_strength_3 = desired_strength_2 - strength_2
                    for ingredient_3, strength_3 in ingredients_strengths:
                        if strength_3 == desired_strength_3:
                            combination = IngredientCombination()
                            combination.add(ingredient, strength//25)
                            combination.add(ingredient_2, strength_2//25)
                            combination.add(ingredient_3, strength_3//25)
                            choices.add(combination)
                        elif strength_3 < desired_strength_3:
                            desired_strength_4 = desired_strength_3 - strength_3
                            for ingredient_4, strength_4 in ingredients_strengths:
                                if strength_4 == desired_strength_4:
                                    combination = IngredientCombination()
                                    combination.add(ingredient, strength//25)
                                    combination.add(ingredient_2, strength_2//25)
                                    combination.add(ingredient_3, strength_3//25)
                                    combination.add(ingredient_4, strength_4//25)
                                    choices.add(combination)
    return choices

if __name__ == '__main__':
    print()
    ingredient_combinations = get_ingredients_choices("red", 75)
    
    for combination in ingredient_combinations:
        # Sanity check: is 3x Fire Quartz here?
        is_it_here = False
        for ingredient, quantity in combination.combination:
            if ingredient.name == "Fire Quartz" and quantity == 3:
                is_it_here = True
                break
        if is_it_here:
            print(combination)
            break