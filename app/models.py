from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Date, String, ForeignKey, Float, Table, Column, Integer


class Base(DeclarativeBase):
    pass



db = SQLAlchemy(model_class = Base)





service_mechanics = Table(
    "service_mechanics",
    Base.metadata,
    Column("service_tickets_id",Integer, ForeignKey("service_tickets.id")),
    Column("mechanics_id",Integer, ForeignKey("mechanics.id"))
)

class Customers(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(160),nullable=False)
    last_name: Mapped[str] = mapped_column(String(160),nullable=False)
    email: Mapped[str] = mapped_column(String(360), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(500),nullable=False)
    password: Mapped[str] = mapped_column(String(120),nullable=False)
    username: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    
    service_ticket: Mapped[list['ServiceTickets']] = relationship('ServiceTickets', back_populates='customer')

class ServiceTickets(Base):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    service_date: Mapped[date] = mapped_column(Date, default=datetime.now)
    service_description: Mapped[str] = mapped_column(String(2000),nullable=False)
    price: Mapped[float] = mapped_column(Float(20), nullable=False)
    vin: Mapped[str] = mapped_column(String(50),nullable=False)

    
    customer: Mapped["Customers"] = relationship("Customers", back_populates="service_ticket")
    mechanic: Mapped[list["Mechanics"]] = relationship("Mechanics", secondary=service_mechanics, back_populates="service_ticket")

class Mechanics(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(160),nullable=False)
    last_name: Mapped[str] = mapped_column(String(160),nullable=False)
    email: Mapped[str] = mapped_column(String(360), unique=True, nullable=False)
    salary: Mapped[float] = mapped_column(Float(20), nullable=False)
    address: Mapped[str] = mapped_column(String(500),nullable=False)
    password: Mapped[str] = mapped_column(String(120),nullable=False)

    service_ticket: Mapped[list["ServiceTickets"]] = relationship("ServiceTickets",secondary=service_mechanics, back_populates="mechanic")