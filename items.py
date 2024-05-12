from dataclasses import dataclass
from typing import Literal, List

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

class IngredientCombination:
    def __init__(self):
        self.combination: set[tuple[IngredientItem, int]] = set()

    def add(self, ingredient: IngredientItem, quantity: int):
        # Check if the ingredient is already in the combination
        for ingredient_, quantity_ in self.combination:
            if ingredient_ == ingredient:
                self.combination.remove((ingredient_, quantity_))
                quantity += quantity_
                break
        self.combination.add((ingredient, quantity))

    # To avoid duplicates, we need to make Python tread the combination of (A, B) and (B, A) as the same combination
    def __eq__(self, other):
        if not isinstance(other, IngredientCombination):
            return False
        
        if len(self.combination) != len(other.combination):
            return False
        
        for ingredient, quantity in self.combination:
            if (ingredient, quantity) not in other.combination:
                return False
            
        return True
    
    def __hash__(self):
        # Sort combinations by ingredient name, then by quantity
        sorted_combination = sorted(self.combination, key=lambda x: (x[0].name, x[1]))
        return hash(tuple(sorted_combination))

    def __str__(self):
        s = ""
        for ingredient, quantity in self.combination:
            qty_modifier = f"{quantity}x " if quantity > 1 else ""
            s += f"{qty_modifier}{ingredient.name}"
            s += " + "
        return s[:-3]