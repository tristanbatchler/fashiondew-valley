from bs4 import BeautifulSoup
import requests
from items import TailoringItem, IngredientItem
from typing import List


def _get_tailoring_data() -> List[TailoringItem]:

    items = []

    base = "https://stardewvalleywiki.com/"
    wiki_url = base + "Tailoring"
    response = requests.get(wiki_url)

    if response.status_code == 200:
        print("Successfully downloaded Tailoring page")
    else:
        # print("Failed to download Tailoring page")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # All data we want is in tables with the class "wikitable". The first table is for shirts, the second for pants, and the third for hats.
    tables = soup.find_all("table", class_="wikitable")
    for table_idx, table in enumerate(tables):
        if table_idx > 2:
            break  # Other tables at the end are not relevant

        # Shirst have 5 columns, pants have 4, and hats have 3
        ingredients_column = 5 if table_idx == 0 else 4 if table_idx == 1 else 3

        for row in table.find_all("tr"):
            if row.find("th"):
                continue
            tailoring_item: TailoringItem = TailoringItem(type=["shirt", "pants", "hat"][table_idx], ingredients=[])
            for i, cell in enumerate(row.find_all("td")):

                    if i == 0:
                        tailoring_item.image_url = base + cell.find("img")["src"]
                    elif i == 1:
                        tailoring_item.name = cell.get_text()
                    elif i == 3 and table_idx != 2:  # Hats don't have a dyeable column
                        tailoring_item.dyeable = "Yes" in cell.get_text()
                    elif i == ingredients_column:
                        # image_url is in the img tag, name is in the a tag
                        tailoring_item.ingredients = []
                        for ingredient in cell.find_all("span"):
                            ingredient_item = IngredientItem()
                            ingredient_item.image_url = base + ingredient.find("img")["src"]
                            ingredient_item.name = ingredient.find("a").get_text()
                            tailoring_item.ingredients.append(ingredient_item)
            # There are a lot of duplicates
            names_so_far = [item.name for item in items]
            if tailoring_item.name in names_so_far:
                tailoring_item.name = f"{tailoring_item.image_url.split('/')[-1].split('.')[0]}"
            

            items.append(tailoring_item)
    return items



tailoring_data = _get_tailoring_data()