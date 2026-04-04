from sqlalchemy import UniqueConstraint, create_engine, Column, String, Integer, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()


# 1. Users Table
class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30), nullable=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=True)
    business_name = Column(String(50), nullable=True)
    business_address = Column(String(50), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Products", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transactions", back_populates="user", cascade="all, delete-orphan")


# 2. Products Table
class Products(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)
    cost_price = Column(Float)
    selling_price = Column(Float)

    supplier = Column(String(100))
    img_url = Column(String(255))
    description = Column(String(255))

    buy_date = Column(DateTime)
    expiry_date = Column(DateTime)

    user = relationship("Users", back_populates="products")
    transaction_items = relationship("TransactionItem", back_populates="product")
    
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_product_name"),
    )


# 3. Transactions Table
class Transactions(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    amount = Column(Float, nullable=False)
    transaction_type = Column(String(50))  # order or walk-in
    payment_method = Column(String(50))    # cash, card, transfer
    payment_status = Column(String(50))    # paid, unpaid

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Users", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


# 4. Transaction Items Table
class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, autoincrement=True)

    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)

    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    transaction = relationship("Transactions", back_populates="items")
    product = relationship("Products", back_populates="transaction_items")

    def __repr__(self):
        return f"<TransactionItem(product={self.product_name}, qty={self.quantity}, subtotal={self.subtotal})>"
    

# 5. OTP table
class OTP(Base):
    __tablename__ = "otp_table"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    otp_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)


Base.metadata.create_all(engine)