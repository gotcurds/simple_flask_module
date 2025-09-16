from app.extensions import ma
from app.models import InventoryPartDescription

class InventoryPartDescriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InventoryPartDescription
        load_instance = False

inventory_part_description_schema = InventoryPartDescriptionSchema()
inventory_part_descriptions_schema = InventoryPartDescriptionSchema(many=True)