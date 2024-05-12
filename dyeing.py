from bs4 import BeautifulSoup
import requests
from items import IngredientItem, IngredientCombination
import itertools

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



def get_ingredients_choices(desired_color: str, desired_strength: int, favour: list[IngredientItem] | None = None) -> list[IngredientCombination]:
    """The return value represents the choices the user has available. Each choice is an ingredient or combination of ingredients that can be used to achieve the desired color and strength."""
    
    choices = []
    
    if favour is None:
        favour = []

    ingredients_for_color = dyeing_info[desired_color]["ingredients"]

    # Use as many of the favoured ingredients as possible first
    common_ingredients_strengths = {}
    for favoured_ing in favour:
        if favoured_ing in ingredients_for_color:
            common_ingredients_strengths[favoured_ing] = ingredients_for_color[favoured_ing]

    print(f"Attempting to use as many of these ingredients as possible: {', '.join([ingredient.name for ingredient in common_ingredients_strengths.keys()])}")

    # Use the favored ingredients
    for r in range(1, len(common_ingredients_strengths) + 1):
        for combination in itertools.combinations(common_ingredients_strengths.items(), r):
            total_strength = sum(strength for _, strength in combination)
            if total_strength == desired_strength:
                new_combination = IngredientCombination()
                for ingredient, strength in combination:
                    new_combination.add(ingredient, strength//25)
                choices.append(new_combination)
            elif total_strength < desired_strength:
                remaining_strength = desired_strength - total_strength
                for ingredient, strength in ingredients_for_color.items():
                    if strength == remaining_strength:
                        new_combination = IngredientCombination()
                        for ing, strng in combination:
                            new_combination.add(ing, strng//25)
                        new_combination.add(ingredient, strength//25)
                        choices.append(new_combination)
                    elif strength < remaining_strength:
                        for ingredient_2, strength_2 in ingredients_for_color.items():
                            if strength + strength_2 == remaining_strength:
                                new_combination = IngredientCombination()
                                for ing, strng in combination:
                                    new_combination.add(ing, strng//25)
                                new_combination.add(ingredient, strength//25)
                                new_combination.add(ingredient_2, strength_2//25)
                                choices.append(new_combination)

   # Now, use the remaining ingredients
    ingredients_strengths = ingredients_for_color.items()
    
    for ingredient, strength in ingredients_strengths:
        if strength == desired_strength:
            combination = IngredientCombination()
            combination.add(ingredient, strength//25)
            choices.append(combination)
        elif strength < desired_strength:
            desired_strength_2 = desired_strength - strength
            for ingredient_2, strength_2 in ingredients_strengths:
                if strength_2 == desired_strength_2:
                    combination = IngredientCombination()
                    combination.add(ingredient, strength//25)
                    combination.add(ingredient_2, strength_2//25)
                    choices.append(combination)
                elif strength_2 < desired_strength_2:
                    desired_strength_3 = desired_strength_2 - strength_2
                    for ingredient_3, strength_3 in ingredients_strengths:
                        if strength_3 == desired_strength_3:
                            combination = IngredientCombination()
                            combination.add(ingredient, strength//25)
                            combination.add(ingredient_2, strength_2//25)
                            combination.add(ingredient_3, strength_3//25)
                            choices.append(combination)
    
    # Remove duplicates
    return list(dict.fromkeys(choices))


if __name__ == '__main__':
    import random
    print()
    red_ingredients = dyeing_info["red"]["ingredients"]
    random_red_ingredients = random.sample([(ingredient, strength) for ingredient, strength in red_ingredients.items()], 5)
    print("Random red ingredients:")
    for ingredient, strength in random_red_ingredients:
        print(f"{ingredient.name} ({strength}%)")

    ingredient_combinations = get_ingredients_choices("red", 75, favour=[ingredient for ingredient, _ in random_red_ingredients])

    # Should be 11,800 combinations or so
    if len(ingredient_combinations) != 11800:
        print("WARNING: The number of combinations is not as expected. Got", len(ingredient_combinations))
    
    # Sanity check: is 3x Fire Quartz here?
    few = 10
    is_it_here = False
    print("Here's what we got...")
    for i, combination in enumerate(ingredient_combinations):
        if i < few:
            print(" + ".join([f"{quantity}x {ingredient.name}" for ingredient, quantity in combination.combination]))
        
        for ingredient, quantity in combination.combination:
            if ingredient.name == "Fire Quartz" and quantity == 3:
                is_it_here = True
                break
        if is_it_here:
            break
    
    if not is_it_here:
        print("WARNING: 3x Fire Quartz is not here.")