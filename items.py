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