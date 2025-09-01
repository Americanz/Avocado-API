"""
Poster client model
"""


from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    Boolean,
    Text,
    Integer,
    Numeric,
    JSON,
)

from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel


class Client(BaseModel):
    """
    Poster client data for bonus system integration
    Maps to clients.getClients API response
    """

    __tablename__ = "clients"

    use_generic_routes = True
    search_fields = ["phone", "email", "firstname", "lastname"]
    default_order_by = ["-created_at"]

    # Poster client info
    client_id = Column(
        BigInteger, unique=True, nullable=False, index=True, comment="Poster client ID"
    )

    # Personal information
    firstname = Column(String(100), nullable=True, comment="Client first name")
    lastname = Column(String(100), nullable=True, comment="Client last name")
    patronymic = Column(String(100), nullable=True, comment="Client patronymic")

    # Contact information
    phone = Column(String(20), nullable=True, index=True, comment="Client phone")
    phone_number = Column(String(20), nullable=True, comment="Phone number without +")
    email = Column(String(255), nullable=True, comment="Client email")

    # Personal details
    birthday = Column(String(20), nullable=True, comment="Client birthday (YYYY-MM-DD)")
    client_sex = Column(String(10), nullable=True, comment="Client gender (0/1)")

    # Address information
    country = Column(String(100), nullable=True, comment="Country")
    city = Column(String(100), nullable=True, comment="City")
    address = Column(Text, nullable=True, comment="Full address")
    addresses = Column(JSON, nullable=True, comment="Array of addresses")

    # Business information
    card_number = Column(String(50), nullable=True, comment="Card number")
    comment = Column(Text, nullable=True, comment="Comment about client")

    # Financial and loyalty info
    discount_per = Column(
        Numeric(5, 2), nullable=True, comment="Personal discount percentage"
    )
    bonus = Column(Numeric(10, 2), nullable=True, comment="Current bonus balance")
    total_payed_sum = Column(Numeric(10, 2), nullable=True, comment="Total paid amount")

    # Group and loyalty program
    client_groups_id = Column(Integer, nullable=True, comment="Client group ID")
    client_groups_name = Column(String(255), nullable=True, comment="Client group name")
    client_groups_discount = Column(
        Numeric(5, 2), nullable=True, comment="Group discount percentage"
    )
    loyalty_type = Column(Integer, nullable=True, comment="Loyalty type")
    birthday_bonus = Column(
        Numeric(10, 2), nullable=True, comment="Birthday bonus amount"
    )

    # System fields
    date_activale = Column(DateTime, nullable=True, comment="Activation date")
    delete = Column(Boolean, default=False, comment="Is deleted")
    ewallet = Column(Numeric(10, 2), nullable=True, comment="E-wallet balance")

    # Link to Telegram user
    telegram_user_id = Column(
        BigInteger, nullable=True, index=True, comment="Linked Telegram user ID"
    )

    # Telegram profile data
    telegram_username = Column(String(255), nullable=True, comment="Telegram @username")
    telegram_first_name = Column(
        String(255), nullable=True, comment="Telegram first name"
    )
    telegram_last_name = Column(
        String(255), nullable=True, comment="Telegram last name"
    )
    telegram_language_code = Column(
        String(10), nullable=True, default="uk", comment="Telegram language"
    )
    is_telegram_active = Column(Boolean, default=False, comment="Is bot active")
    telegram_joined_at = Column(DateTime, nullable=True, comment="When joined bot")
    telegram_last_activity = Column(
        DateTime, nullable=True, comment="Last bot activity"
    )

    # Store raw API response
    raw_data = Column(JSON, nullable=True, comment="Original API response data")

    # Sync status
    last_sync_from_poster = Column(
        DateTime, nullable=True, comment="Last sync from Poster"
    )

    bonus_history = relationship("TransactionBonus", back_populates="client_details")

    def __repr__(self):
        return f"<Client poster_id={self.client_id} phone={self.phone}>"
