from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from src.core.models.base_model import BaseModel


class BonusAccount(BaseModel):
    __tablename__ = "bonus_accounts"

    use_generic_routes = True
    search_fields = ["client_id"]
    default_order_by = ["-created_at"]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    balance = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BonusAccount client_id={self.client_id} balance={self.balance}>"


class Transaction(BaseModel):
    __tablename__ = "bonus_transactions"

    use_generic_routes = True
    search_fields = ["client_id", "type"]
    default_order_by = ["-created_at"]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_id = Column(
        UUID(as_uuid=True), ForeignKey("bonus_accounts.id"), nullable=False
    )
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # 'accrual' або 'debit'
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    account = relationship("BonusAccount", backref="transactions")

    def __repr__(self):
        return f"<Transaction client_id={self.client_id} amount={self.amount} type={self.type}>"


__all__ = ["BonusAccount", "Transaction"]
