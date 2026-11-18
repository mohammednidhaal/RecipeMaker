from typing import Optional
from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str = Field(..., description="Name of the ingredient (e.g., 'chicken breast', 'olive oil')")
    quantity: float = Field(..., description="Numerical quantity or weight of the ingredient")
    unit: str = Field(..., description="Measurement unit (e.g., 'g', 'kg', 'ml', 'tbsp', 'tsp', 'pieces', 'slices', 'cloves')")
    notes: Optional[str] = Field(None, description="Optional preparation notes (e.g., 'diced', 'minced')")

    def scale(self, factor: float) -> "Ingredient":
        """Return a new scaled ingredient."""
        scaled_quantity = round(self.quantity * factor, 2)
        # Avoid float formatting artifacts like 2.0 -> 2
        if scaled_quantity.is_integer():
            scaled_quantity = int(scaled_quantity)
        return Ingredient(
            name=self.name,
            quantity=scaled_quantity,
            unit=self.unit,
            notes=self.notes
        )
