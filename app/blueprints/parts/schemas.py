from app.extensions import ma
from app.models import InventoryPartDescription, Part
from marshmallow import fields

class InventoryPartDescriptionSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = InventoryPartDescription
        load_instance = False 
        
inventory_part_description_schema = InventoryPartDescriptionSchema()
inventory_part_descriptions_schema = InventoryPartDescriptionSchema(many=True)

class PartSchema(ma.SQLAlchemyAutoSchema):
    # This nested field will serialize the related InventoryPartDescription
    inventory_description = fields.Nested(InventoryPartDescriptionSchema, dump_only=True)

    class Meta:
        model = Part
        load_instance = False
        # Ensure that the desc_id foreign key is included in the serialized output
        include_fk = True

part_schema = PartSchema()
parts_schema = PartSchema(many=True)