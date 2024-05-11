from PIL import Image
import blend_modes
import numpy
import math
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import *
from pathlib import Path
import os
import tkinter as tk
from tkinter import ttk


CWD = Path(__file__).parent

colors = {
    "aquamarine": (127,255,212),
    "black": (45,45,45),
    "blue": (46,85,183),
    "brown": (130,73,37),
    "copper": (179,85,0),
    "cyan": (0,255,255),
    "dark blue": (0,0,139),
    "dark brown": (139,69,19),
    "dark gray": (169,169,169),
    "dark green": (0,100,0),
    "dark pink": (255,20,147),
    "dark purple": (148,0,211),
    "dark red": (139,0,0),
    "dark yellow": (184,134,11),
    "gold": (255,215,0),
    "gray": (128,128,128),
    "green": (10,143,0),
    "iridium": (105,15,255),
    "iron": (197,213,224),
    "jade": (130,158,93),
    "light cyan": (180,255,255),
    "lime": (0,255,0),
    "orange": (255,128,0),
    "pale violet red": (219,112,147),
    "pink": (255,163,186),
    "poppyseed": (82,47,153),
    "purple": (115,41,181),
    "red": (220,0,0),
    "salmon": (255,85,95),
    "sand": (255,222,173),
    "white": (255,255,255),
    "yellow": (255,230,0),
    "yellow green": (173,255,47)
}

def map_between(value, start1, stop1, start2, stop2):
    return start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1))

def logistical_map(x, L, k, x0):
    return L / (1 + math.exp(-k*(x - x0)))

def dye_image(base_image_path: Path, color_name, strength):
    """
    Takes a transparent image and dyes it with the specified color. To do this, first the base 
    image is converted to grayscale, then a solid color image with the same size/edges is overlaid 
    on top of the grayscale image with a blend mode of "overlay". The result is saved to the output 
    path.
    """

    color = colors[color_name]

    output_path = base_image_path.parent / f"{color_name}_{strength}.png"

    if output_path.exists():
        # print(f"Skipping {output_path} (already exists)")
        return

    # Open base image
    base_image = Image.open(base_image_path)

    base_image_gray = numpy.array(base_image.convert('L').convert('RGBA')).astype('float')

    # Get the max value of the grayscale image (ignoring transparent pixels)
    max_value = 0
    for row in base_image_gray:
        for pixel in row:
            if pixel[3] > 0 and pixel[0] > max_value:
                max_value = pixel[0]

    # Lighten the grayscale image until its new max_value is 255 (careful to preserve transparency)
    lightened_base_image_gray = numpy.copy(base_image_gray)
    for i in range(len(lightened_base_image_gray)):
        for j in range(len(lightened_base_image_gray[i])):
            if lightened_base_image_gray[i][j][3] > 0:
                lightened_base_image_gray[i][j][0] = map_between(lightened_base_image_gray[i][j][0], 0, max_value, 0, 255)
    
    # Create a solid color image with the same size as the base image
    solid_color_raw = Image.new('RGBA', base_image.size, color)

    # Convert to float array (required for blend_modes)
    solid_color = numpy.array(solid_color_raw).astype('float')

    # Blend the grayscale image with the solid color image using the "overlay" blend mode
    lightness_score = logistical_map(max_value, 0.85, -0.07, 132) + 0.15
    strength_score = map_between(strength, 25, 100, 1.25, 2)

    opacity_0 = lightness_score * strength_score
    blend_opacity = opacity_0 + (strength / 25 - 1) * (1 - opacity_0) / 3

    # print(f"{base_image_path} got max value of {max_value}, so a lightness score of {lightness_score} resulting in a blend opacity of {blend_opacity}")

    result_image = numpy.uint8(blend_modes.multiply(base_image_gray, solid_color, min(blend_opacity, 1)))

    # Save the result image

    Image.fromarray(result_image).save(output_path)

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

@dataclass
class IngredientItem:
    name: str | None = None
    image_url: str | None = None

    def __hash__(self):
        return hash(self.name)

@dataclass
class TailoringItem:
    name: str | None = None
    image_url: str | None = None
    type: Literal["shirt", "pants", "hat"] | None = None
    ingredients: List[IngredientItem] | None = None
    dyeable: bool | None = None

class CharacterCreator(tk.Tk):
    def __init__(self, tailoring_data: List[TailoringItem]):
        super().__init__()

        self.title("Character Creator")
        self.geometry("960x640")

        self.tailoring_data = tailoring_data

        self.color_currently_selected = None
        self.create_widgets()
        self.tab_control.bind("<<NotebookTabChanged>>", lambda event: self.update_tab_control_list(self.tab_control.select()))

        self.shirt_color = None
        self.pants_color = None
        self.hat_color = None

        self.shirt_selected = None
        self.pants_selected = None
        self.hat_selected = None
        self.item_currently_selected = None

        self.shirt_strength = 0
        self.pants_strength = 0
        self.hat_strength = 0

        self.shirt_img = None
        self.pants_img = None
        self.hat_img = None

    def create_widgets(self):
        # Top left: Character Portrait
        self.character_canvas = tk.Canvas(self, width=320, height=320)
        self.character_canvas.grid(row=0, column=0, padx=10, pady=10)

        # Top right: Tabs for Shirt, Pants, and Hat
        self.tab_control = ttk.Notebook(self)
        
        self.shirt_tab = ttk.Frame(self.tab_control)
        self.pants_tab = ttk.Frame(self.tab_control)
        self.hat_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.shirt_tab, text="Shirt")
        self.tab_control.add(self.pants_tab, text="Pants")
        self.tab_control.add(self.hat_tab, text="Hat")

        self.tab_control.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Add a grid of tailorable items to each page in the notebook
        self.notebook_page = tk.Canvas(self.tab_control, width=480, height=240)
        self.notebook_page_frame = tk.Frame(self.notebook_page)
        self.notebook_page_scrollbar = tk.Scrollbar(self.tab_control, orient="vertical", command=self.notebook_page.yview)
        self.notebook_page.configure(yscrollcommand=self.notebook_page_scrollbar.set)

        self.notebook_page_scrollbar.grid(row=0, column=1, padx=(0,10), pady=10, sticky="ns")
        self.notebook_page.grid(row=0, column=0, padx=10, pady=42, sticky="nsew")
        self.notebook_page.create_window((0, 0), window=self.notebook_page_frame, anchor="nw")

        # Under the notebook page: Show only dyeable items checkbox
        self.show_only_dyeable_var = tk.IntVar()
        self.show_only_dyeable_checkbox = tk.Checkbutton(self, text="Show only dyeable items", variable=self.show_only_dyeable_var, command=self.update_tab_control_list)
        self.show_only_dyeable_checkbox.grid(row=1, column=1, padx=10, pady=10, sticky="nw")


        # Middle left: Color Palette
        self.color_palette = tk.Frame(self)
        self.color_palette.grid(row=1, column=0, padx=10, pady=10)

        # Bottom left: Value Slider
        self.value_slider = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL, length=320, label="Dye strength (%)")
        self.value_slider.grid(row=2, column=0, padx=10, pady=10)

        # Bottom middle: Scrollable list of ingredients
        self.ingredients_list = tk.Listbox(self, width=30, height=10)
        self.ingredients_list.grid(row=2, column=1, padx=10, pady=10)

        # Bottom right: Scrollable list of image icons and their names
        self.icons_list = tk.Listbox(self, width=30, height=10)
        self.icons_list.grid(row=2, column=2, padx=10, pady=10)

        # Top left: Character portrait (blank if file not found)
        portrait_path = Path(CWD / "images" / "default.png")
        if portrait_path.exists():
            self.character_image = tk.PhotoImage(file="images/default.png")
        else:
            self.character_image = tk.PhotoImage(width=32, height=32)
        # Zoom the character portait image to 4x
        self.character_image = self.character_image.zoom(4, 4)

        self.character_canvas.create_image(150, 200, image=self.character_image)


        # Example usage of updating color palette
        self.update_color_palette()

        self.value_slider.set(0)
        
        # Only allow the slider to move in increments of 25
        self.value_slider.config(resolution=25)

        # Hook up the slider to update the tab control list and 
        self.value_slider.bind("<ButtonRelease-1>", self.update_tab_control_list_and_character_display)

        # Example usage of ingredients list
        ingredients = ["Ingredient 1", "Ingredient 2", "Ingredient 3", "Ingredient 4", "Ingredient 5"]
        for ingredient in ingredients:
            self.ingredients_list.insert(tk.END, ingredient)

        # Example usage of icons list
        icons = ["Icon 1", "Icon 2", "Icon 3", "Icon 4", "Icon 5"]
        for icon in icons:
            self.icons_list.insert(tk.END, icon)

    def update_color_palette(self):
        columns = 11
        for i, color in enumerate(colors):
            r, g, b = colors[color]
            color_button = tk.Button(self.color_palette, bg=f"#{r:02x}{g:02x}{b:02x}", width=2, height=1, command=lambda color=color: self.select_color(color))
            color_button.grid(row=i // columns, column=i % columns, padx=5, pady=5)

            if self.color_currently_selected == color:
                color_button.config(relief=tk.SUNKEN)

    def update_tab_control_list_and_character_display(self, event=None):
        if self.value_slider.get() == 0:
            self.color_currently_selected = None
        self.set_selection_image(self.item_currently_selected.type)
        self.update_tab_control_list()
        self.update_character_display()

    def select_color(self, color):
        tab_name = self.tab_control.tab(self.tab_control.select(), "text").lower()
        if self.shirt_selected is not None and tab_name == "shirt":
            self.item_currently_selected = self.shirt_selected
        elif self.pants_selected is not None and tab_name == "pants":
            self.item_currently_selected = self.pants_selected
        elif self.hat_selected is not None and tab_name == "hat":
            self.item_currently_selected = self.hat_selected

        self.color_currently_selected = color
        if self.item_currently_selected:
            self.set_selection_image(self.item_currently_selected.type)
        self.update_tab_control_list_and_character_display()
        self.update_color_palette()

    def update_tab_control_list(self, event=None):
        tab_label = self.tab_control.tab(self.tab_control.select(), "text")
        tab_name = tab_label.lower()
        
        if self.item_currently_selected and tab_name != self.item_currently_selected.type:
            self.item_currently_selected = None
        elif self.shirt_selected and tab_name == "shirt":
            self.item_currently_selected = self.shirt_selected
        elif self.pants_selected and tab_name == "pants":
            self.item_currently_selected = self.pants_selected
        elif self.hat_selected and tab_name == "hat":
            self.item_currently_selected = self.hat_selected

        # Clear the current list of items
        for widget in self.notebook_page_frame.winfo_children():
            widget.destroy()

        # Scrollable grid of selectable tailorable items (icon + name) based on tab selection
        itemno = -1
        for item in self.tailoring_data:
            if self.show_only_dyeable_var.get() and not item.dyeable:
                continue

            if item.type == tab_name:
                itemno += 1
                variant = "original.png"
                if item.dyeable and self.color_currently_selected is not None and self.value_slider.get() > 0:
                    variant = self.color_currently_selected + "_" + str(self.value_slider.get()) + ".png"

                icon_img_path = Path(CWD / "images" / item.type / sanitize_name(item.name) / variant)
                icon_img = tk.PhotoImage(file=icon_img_path)
                icon_img = icon_img.zoom(2, 2)
                button = tk.Button(self.notebook_page_frame, text=item.name, image=icon_img, compound=tk.TOP, command=lambda item=item: self.select_item(item))
                button.image = icon_img
                columns = 4
                button.grid(row=itemno // columns, column=itemno % columns, padx=5, pady=5)

                if item.type == "shirt" and self.shirt_selected == item:
                    button.config(relief=tk.SUNKEN)
                elif item.type == "pants" and self.pants_selected == item:
                    button.config(relief=tk.SUNKEN)
                elif item.type == "hat" and self.hat_selected == item:
                    button.config(relief=tk.SUNKEN)

        self.notebook_page_frame.update_idletasks()
        self.notebook_page.config(scrollregion=self.notebook_page.bbox("all"))

    def select_item(self, item: TailoringItem):
        # print(f"Selected {item.name}")
        if item.type == "shirt":
            self.shirt_selected = item
        elif item.type == "pants":
            self.pants_selected = item
        elif item.type == "hat":
            self.hat_selected = item
        self.item_currently_selected = item

        self.set_selection_image(item.type)
        self.update_tab_control_list_and_character_display()

    def set_selection_image(self, type):
        if self.item_currently_selected is not None:
            variant = "original.png"
            if self.item_currently_selected.dyeable and self.color_currently_selected is not None and self.value_slider.get() > 0:
                variant = self.color_currently_selected + "_" + str(self.value_slider.get()) + ".png"

            img_path = Path(CWD / "images" / type / sanitize_name(self.item_currently_selected.name) / variant)
            img = tk.PhotoImage(file=img_path)
            img = img.zoom(4, 4)

            if type == "shirt":
                self.shirt_img = img
            elif type == "pants":
                self.pants_img = img
            elif type == "hat":
                self.hat_img = img

    def update_character_display(self):
        # print("Updating character display")

        current_item_name = self.item_currently_selected.name if self.item_currently_selected else "None"
        current_color = self.color_currently_selected if self.color_currently_selected else "original"
        shirt_selected_name = self.shirt_selected.name if self.shirt_selected else "None"
        shirt_color = self.shirt_color if self.shirt_color else "original"
        pants_selected_name = self.pants_selected.name if self.pants_selected else "None"
        pants_color = self.pants_color if self.pants_color else "original"
        print(f"Item just selected: {current_item_name} ({current_color})")
        print(f"Current shirt: {shirt_selected_name} ({shirt_color})")
        print(f"Current pants: {pants_selected_name} ({pants_color})")

        current_tab = self.tab_control.tab(self.tab_control.select(), "text").lower()


        # Combine the images
        if self.shirt_img is not None:
            self.shirt_display = self.character_canvas.create_image(150, 216, image=self.shirt_img)
        if self.pants_img is not None:
            self.pants_display = self.character_canvas.create_image(150, 242, image=self.pants_img)
        if self.hat_img is not None:
            self.hat_display = self.character_canvas.create_image(150, 176, image=self.hat_img)
       
        self.character_canvas.update()


def get_tailoring_data() -> List[TailoringItem]:

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
        for row in table.find_all("tr"):
            if row.find("th"):
                continue
            tailoring_item: TailoringItem = TailoringItem(type=["shirt", "pants", "hat"][table_idx], ingredients=[])
            for i, cell in enumerate(row.find_all("td")):
                match i:
                    case 0:
                        tailoring_item.image_url = base + cell.find("img")["src"]
                    case 1:
                        tailoring_item.name = cell.get_text()
                    case 3:
                        tailoring_item.dyeable = "Yes" in cell.get_text()
                    case 5:
                        # image_url is in the img tag, name is in the a tag
                        tailoring_item.ingredients = []
                        ingredient_image = cell.find("img")
                        if ingredient_image:
                            ingredient_image_url = base + ingredient_image["src"]
                            ingredient_name = cell.find("a").get_text()
                            tailoring_item.ingredients.append(IngredientItem(name=ingredient_name, image_url=ingredient_image_url))

            # There are a lot of duplicates
            names_so_far = [item.name for item in items]
            if tailoring_item.name in names_so_far:
                tailoring_item.name = f"{tailoring_item.image_url.split('/')[-1].split('.')[0]}"
            

            items.append(tailoring_item)
    return items

def main():
    tailoring_data = get_tailoring_data()

    for item in tailoring_data:
        img_path = Path(CWD / "images" / item.type / sanitize_name(item.name) / "original.png")

        # Download the original image
        if not img_path.exists():
            reduce = 3 if item.type == "hat" else 4
            download_image(item.image_url, img_path, reduce_size_by=reduce)
        
        # Get the dyed versions of the image
        for color in colors:
            for strength in [25, 50, 75, 100]:
                if item.dyeable:
                    dye_image(img_path, color, strength)

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

    # Start the GUI
    app = CharacterCreator(tailoring_data)
    app.mainloop()

if __name__ == '__main__':
    main()