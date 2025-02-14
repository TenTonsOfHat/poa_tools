from pydantic import BaseModel, Field
from typing import Optional

class PropertyRecord(BaseModel):
    """Represents a property record with associated details."""
    address: Optional[str] = Field(None, description="Street address of the property")
    mail_address: Optional[str] = Field(None, alias="Mail Address", description="Mailing address for the property owner")
    owner: Optional[str] = Field(None, alias="Owner", description="Name of the property owner")
    subdivision: Optional[str] = Field(None, alias="Sub", description="Subdivision name")
    city: Optional[str] = Field(None, alias="City", description="City where the property is located")
    assessed_value: Optional[str] = Field(None, alias="Assessed Value", description="Assessed value of the property")
    str_location: Optional[str] = Field(None, alias="S-T-R", description="Section-Township-Range location")
    block_lot: Optional[str] = Field(None, alias="Block / Lot", description="Block and lot numbers")
    acres: Optional[str] = Field(None, alias="Acres", description="Property size in acres")
    legal: Optional[str] = Field(None, alias="Legal", description="Legal description of the property")

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            # Add any custom encoders if needed
        } 