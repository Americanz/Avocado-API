"""
Pydantic schemas for Transaction model
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TransactionBase(BaseModel):
    """Base schema for Transaction"""

    # Basic transaction info
    transaction_id: int = Field(..., description="Poster transaction ID")
    spot_id: int = Field(..., description="Spot ID from Poster")

    # Link to Poster spot
    spot: Optional[int] = Field(None, description="Link to Poster spot")

    # Client information
    client_id: Optional[int] = Field(None, description="Poster client ID")
    client: Optional[int] = Field(None, description="Link to Poster client")

    # Transaction details
    table_id: Optional[int] = Field(None, description="Table ID")

    # Dates and times
    date_start: Optional[datetime] = Field(None, description="Transaction start time")
    date_close: Optional[datetime] = Field(None, description="Transaction close time")

    # Financial data
    sum: Decimal = Field(..., description="Total transaction sum")

    # Payment details
    payed_sum: Optional[Decimal] = Field(None, description="Total payment amount")
    payed_cash: Optional[Decimal] = Field(None, description="Cash payment amount")
    payed_card: Optional[Decimal] = Field(None, description="Card payment amount")
    payed_cert: Optional[Decimal] = Field(
        None, description="Certificate payment amount"
    )
    payed_bonus: Optional[Decimal] = Field(None, description="Bonus payment amount")
    payed_third_party: Optional[Decimal] = Field(
        None, description="Third party payment amount"
    )
    round_sum: Optional[Decimal] = Field(None, description="Rounding amount")

    # Payment type and reason
    pay_type: Optional[int] = Field(
        None, description="Payment type: 0-no payment, 1-cash, 2-card, 3-mixed"
    )
    reason: Optional[int] = Field(
        None, description="Reason for closing without payment"
    )

    # Additional charges
    tip_sum: Optional[Decimal] = Field(None, description="Service tip amount")

    # Discounts and bonuses
    discount: Optional[Decimal] = Field(None, description="Discount amount")
    bonus: Optional[Decimal] = Field(None, description="Bonus amount")

    # Fiscal information
    print_fiscal: Optional[int] = Field(
        None, description="Fiscal print flag: 0-no, 1-yes, 2-return"
    )

    # Status and type
    status: int = Field(..., description="Transaction status")

    # Staff information
    user_id: Optional[str] = Field(
        None, description="Poster user ID who created transaction"
    )

    # Raw API response for debugging
    raw_data: Optional[Dict[str, Any]] = Field(
        None, description="Raw API response data"
    )


class TransactionCreate(TransactionBase):
    """Schema for creating Transaction"""

    @field_validator(
        "sum",
        "discount",
        "bonus",
        "payed_sum",
        "payed_cash",
        "payed_card",
        "payed_cert",
        "payed_bonus",
        "payed_third_party",
        "round_sum",
        "tip_sum",
        mode="before",
    )
    @classmethod
    def validate_decimals(cls, v):
        """Convert string/int to Decimal"""
        if v is None:
            return Decimal("0")
        return Decimal(str(v))


class TransactionUpdate(BaseModel):
    """Schema for updating Transaction"""

    # Only fields that can be updated
    spot_id: Optional[int] = None
    spot: Optional[int] = None
    client_id: Optional[int] = None
    client: Optional[int] = None
    table_id: Optional[int] = None
    date_start: Optional[datetime] = None
    date_close: Optional[datetime] = None
    sum: Optional[Decimal] = None

    # Payment fields
    payed_sum: Optional[Decimal] = None
    payed_cash: Optional[Decimal] = None
    payed_card: Optional[Decimal] = None
    payed_cert: Optional[Decimal] = None
    payed_bonus: Optional[Decimal] = None
    payed_third_party: Optional[Decimal] = None
    round_sum: Optional[Decimal] = None
    pay_type: Optional[int] = None
    reason: Optional[int] = None
    tip_sum: Optional[Decimal] = None
    print_fiscal: Optional[int] = None

    discount: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    status: Optional[int] = None
    user_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    @field_validator(
        "sum",
        "discount",
        "bonus",
        "payed_sum",
        "payed_cash",
        "payed_card",
        "payed_cert",
        "payed_bonus",
        "payed_third_party",
        "round_sum",
        "tip_sum",
        mode="before",
    )
    @classmethod
    def validate_decimals(cls, v):
        """Convert string/int to Decimal"""
        if v is None:
            return None
        return Decimal(str(v))


class TransactionResponse(TransactionBase):
    """Schema for Transaction response"""

    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    sync_error: Optional[str] = None
    last_sync_attempt: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionFromPosterAPI(BaseModel):
    """Schema for converting Poster API transaction data to Transaction"""

    # API fields (with different names and types)
    transaction_id: int = Field(..., alias="transaction_id")
    spot_id: int = Field(0, alias="spot_id")
    client_id: Optional[int] = Field(None, alias="client_id")
    table_id: Optional[int] = Field(None, alias="table_id")

    # Date fields (API sends as timestamps or strings)
    date_start: Optional[str] = Field(None, alias="date_start")
    date_close: Optional[str] = Field(None, alias="date_close")

    # Financial fields (API sends as strings)
    sum: Decimal = Field(Decimal("0"), alias="sum")  # Direct mapping: API 'sum' → schema 'sum'
    discount: Decimal = Field(Decimal("0"), alias="discount")
    bonus: Decimal = Field(Decimal("0"), alias="bonus")

    # Payment fields from API
    payed_sum: Optional[Decimal] = Field(None, alias="payed_sum")
    payed_cash: Optional[Decimal] = Field(None, alias="payed_cash")
    payed_card: Optional[Decimal] = Field(None, alias="payed_card")
    payed_cert: Optional[Decimal] = Field(None, alias="payed_cert")
    payed_bonus: Optional[Decimal] = Field(None, alias="payed_bonus")
    payed_third_party: Optional[Decimal] = Field(None, alias="payed_third_party")
    round_sum: Optional[Decimal] = Field(None, alias="round_sum")
    pay_type: Optional[int] = Field(None, alias="pay_type")
    reason: Optional[int] = Field(None, alias="reason")
    tip_sum: Optional[Decimal] = Field(None, alias="tip_sum")
    print_fiscal: Optional[int] = Field(None, alias="print_fiscal")

    # Status and other fields
    status: int = Field(0, alias="status")
    user_id: Optional[str] = Field(None, alias="user_id")

    @field_validator(
        "sum",
        "discount",
        "bonus",
        "payed_sum",
        "payed_cash",
        "payed_card",
        "payed_cert",
        "payed_bonus",
        "payed_third_party",
        "round_sum",
        "tip_sum",
        mode="before",
    )
    @classmethod
    def validate_api_decimals(cls, v):
        """Convert API values to Decimal"""
        if v is None:
            return Decimal("0")
        return Decimal(str(v))

    @field_validator("spot_id", mode="before")
    @classmethod
    def validate_spot_id(cls, v):
        """Convert spot_id to int, required field"""
        if v is None or v == "":
            return 0
        return int(v)

    @field_validator("client_id", "table_id", mode="before")
    @classmethod
    def validate_optional_ints(cls, v):
        """Convert API values to int, handle None for optional fields"""
        if v is None or v == "":
            return None
        return int(v)

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        """Convert status to int, required field"""
        if v is None or v == "":
            return 0
        return int(v)

    def _serialize_for_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Decimal objects to strings for JSON serialization"""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._serialize_for_json(value)  # type: ignore
            elif isinstance(value, list):
                result[key] = [  # type: ignore
                    (
                        self._serialize_for_json(item)
                        if isinstance(item, dict)
                        else str(item) if isinstance(item, Decimal) else item
                    )
                    for item in value
                ]
            else:
                result[key] = value
        return result

    def to_transaction_create(self, original_data: Dict[str, Any]) -> TransactionCreate:
        """Convert to TransactionCreate schema"""

        return TransactionCreate(
            transaction_id=self.transaction_id,
            spot_id=self.spot_id,
            spot=self.spot_id,  # Set both spot_id and spot foreign key
            client_id=self.client_id,
            client=None,  # Will be set separately after client validation
            table_id=self.table_id,
            date_start=None,  # Will be parsed by service
            date_close=None,  # Will be parsed by service
            sum=self.sum,
            payed_sum=self.payed_sum,
            payed_cash=self.payed_cash,
            payed_card=self.payed_card,
            payed_cert=self.payed_cert,
            payed_bonus=self.payed_bonus,
            payed_third_party=self.payed_third_party,
            round_sum=self.round_sum,
            pay_type=self.pay_type,
            reason=self.reason,
            tip_sum=self.tip_sum,
            discount=self.discount,
            bonus=self.bonus,
            print_fiscal=self.print_fiscal,
            status=self.status,
            user_id=self.user_id,
            raw_data=self._serialize_for_json(original_data),  # Store original API data
        )

    def to_transaction_update(self, original_data: Dict[str, Any]) -> TransactionUpdate:
        """Convert to TransactionUpdate schema"""

        return TransactionUpdate(
            spot_id=self.spot_id,
            spot=self.spot_id,  # Set both spot_id and spot foreign key
            client_id=self.client_id,
            client=None,  # Will be set separately after client validation
            table_id=self.table_id,
            date_start=None,  # Will be parsed by service
            date_close=None,  # Will be parsed by service
            sum=self.sum,
            payed_sum=self.payed_sum,
            payed_cash=self.payed_cash,
            payed_card=self.payed_card,
            payed_cert=self.payed_cert,
            payed_bonus=self.payed_bonus,
            payed_third_party=self.payed_third_party,
            round_sum=self.round_sum,
            pay_type=self.pay_type,
            reason=self.reason,
            tip_sum=self.tip_sum,
            discount=self.discount,
            bonus=self.bonus,
            print_fiscal=self.print_fiscal,
            status=self.status,
            user_id=self.user_id,
            raw_data=self._serialize_for_json(original_data),
        )

    class Config:
        populate_by_name = True
