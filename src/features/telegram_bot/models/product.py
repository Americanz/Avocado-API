"""
Poster product model
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    BigInteger,
    Numeric,
    JSON,
)
from src.core.models.base_model import BaseModel


class Product(BaseModel):
    """
    Poster product data from API
    Maps to menu.getProducts API response
    """

    __tablename__ = "products"

    use_generic_routes = True
    search_fields = ["product_name", "barcode", "product_code"]
    default_order_by = ["product_name"]

    # Product identification
    poster_product_id = Column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
        comment="Product ID",
    )
    product_name = Column(String(255), nullable=False, comment="Product name")
    product_code = Column(String(100), nullable=True, comment="Product code")
    barcode = Column(String(100), nullable=True, index=True, comment="Product barcode")

    # Category information
    category_name = Column(String(255), nullable=True, comment="Category name")
    menu_category_id = Column(BigInteger, nullable=True, comment="Menu category ID")

    # Product properties
    unit = Column(String(50), nullable=True, comment="Unit of measurement")
    cost = Column(Numeric(10, 2), nullable=True, comment="Product cost")
    cost_netto = Column(Numeric(10, 2), nullable=True, comment="Product cost netto")
    weight_flag = Column(Boolean, default=False, comment="Weight flag")
    type = Column(Integer, nullable=True, comment="Product type")

    # Visual properties
    color = Column(String(50), nullable=True, comment="Product color")
    photo = Column(Text, nullable=True, comment="Photo path")
    photo_origin = Column(Text, nullable=True, comment="Original photo path")
    sort_order = Column(Integer, default=999, comment="Sort order")

    # Tax information
    tax_id = Column(Integer, nullable=True, comment="Tax ID")
    product_tax_id = Column(Integer, nullable=True, comment="Product tax ID")
    fiscal = Column(Boolean, default=False, comment="Fiscal flag")
    fiscal_code = Column(String(50), nullable=True, comment="Fiscal code")

    # Business rules
    workshop = Column(Integer, nullable=True, comment="Workshop ID")
    nodiscount = Column(Boolean, default=False, comment="No discount flag")
    ingredient_id = Column(BigInteger, nullable=True, comment="Ingredient ID")
    cooking_time = Column(Integer, nullable=True, comment="Cooking time in seconds")
    out = Column(Integer, default=0, comment="Out of stock quantity")

    # Complex data as JSON
    spots = Column(JSON, nullable=True, comment="Spots with prices and visibility")
    sources = Column(JSON, nullable=True, comment="Sources with prices")
    modifications = Column(JSON, nullable=True, comment="Product modifications")
    group_modifications = Column(JSON, nullable=True, comment="Group modifications")
    ingredients = Column(JSON, nullable=True, comment="Product ingredients")

    # Additional fields
    different_spots_prices = Column(
        Boolean, default=False, comment="Different spots prices flag"
    )
    product_production_description = Column(
        Text, nullable=True, comment="Production description"
    )
    hidden = Column(Boolean, default=False, comment="Hidden flag")

    # Store raw API response
    raw_data = Column(JSON, nullable=True, comment="Original API response data")

    def __repr__(self):
        return f"<Product id={self.poster_product_id} name='{self.product_name}'>"
