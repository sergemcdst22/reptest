from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime

from sqlmodel import SQLModel, Field, Session, create_engine


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    fullname: str
    last_bot_message_id: Optional[int] = None
    phone: Optional[str] = None
    current_order_id: Optional[int] = Field(default=None, foreign_key="order.id")


class Igloo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: Optional[str]
    desription: Optional[str]
    photo_local_path: Optional[str]
    photo_link_or_id: Optional[str]


class OrderType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str]
    min_hours_count: int = 0
    total_hours_count: int = 0
    sum_per_hour_12_happy: int = 0
    sum_per_hour_36_happy: int = 0
    sum_per_hour_12: int = 0
    sum_per_hour_36: int = 0
    total_sum: int = 0
    photo_local_path: Optional[str]
    photo_link_or_id: Optional[str]


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    registered_at: str
    removing_at: str
    is_payed: bool = Field(default=False, index=True)
    all_steps_gone: bool = False
    date: Optional[str] = Field(index=True)
    start_time: Optional[str]
    end_time: Optional[str]
    price: Optional[int]
    guests_count: Optional[int]
    needs_call: bool = False
    igloo_id: Optional[int] = Field(default=None, foreign_key="igloo.id", index=True)
    order_type_id: Optional[int] = Field(default=None, foreign_key="ordertype.id")
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")


class Info(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    card_number: Optional[str]
    card_bank: Optional[str]
    card_name: Optional[str]
    






def create_db_and_tables():
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///{sqlite_file_name}"

    engine = create_engine(sqlite_url, echo=True)
    SQLModel.metadata.create_all(engine)
 
    igloo1 = Igloo(name="ТЦ Samarqand Darvoza", address="ул. Коратош, 5А", photo_local_path="i1sd.jpg")  
    igloo2 = Igloo(name="ТЦ Compass", address="Ташкентская кольцевая автомобильная дорога, 17", photo_local_path="i2cm.jpg")
    igloo3 = Igloo(name="ТЦ Riviera", address="ул. Нодиры, 4", photo_local_path="i3rv.jpg")
    plan1 = OrderType(name="Романтическое свидание", total_hours_count=2, total_sum=1100000, photo_local_path="1rom.jpg")
    plan2 = OrderType(name="День рождения / Девичник", total_hours_count=4, total_sum=2500000, photo_local_path="2dr.jpg")
    plan3 = OrderType(name="Аренда без доп. опций", min_hours_count=1, sum_per_hour_12_happy=200000, sum_per_hour_36_happy=300000, 
            sum_per_hour_12=250000, sum_per_hour_36=400000, photo_local_path="3main.jpg")

    info = Info(card_bank="Сбербанк", card_name="Сергей Сергеевич М.", card_number="4276 3801 3321 1073")

    with Session(engine) as session:  
        session.add(igloo1)  
        session.add(igloo2)
        session.add(igloo3)
        session.add(plan1)  
        session.add(plan2)
        session.add(plan3)
        session.add(info)

        session.commit()  # 


if __name__ == "__main__":
    create_db_and_tables()