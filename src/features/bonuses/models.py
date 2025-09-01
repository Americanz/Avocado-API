from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from src.core.models.base_model import BaseModel
import datetime


class User(BaseModel):
    __tablename__ = "users"
    username = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    # ...інші поля...


class BonusAccount(BaseModel):
    __tablename__ = "bonus_accounts"
    client_id = Column(ForeignKey("users.id"), nullable=False)
    balance = Column(Numeric, default=0)
    user = relationship("User")


class Transaction(BaseModel):
    __tablename__ = "bonus_transactions"
    client_id = Column(ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    type = Column(String, nullable=False)  # 'add' або 'remove'
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    admin_id = Column(String, nullable=True)
    user = relationship("User")
