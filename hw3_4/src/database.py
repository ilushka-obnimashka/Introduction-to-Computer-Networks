from datetime import datetime
from typing import Type

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import sessionmaker

from main import MyType


class Base(DeclarativeBase):
    pass


class Catalog(Base):
    __table_name__ = f'{datetime.now().strftime("%y.%m.%d-%H:%M:%S")}.catalogs'
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    image_url: Mapped[str]
    fix_price: Mapped[MyType]
    price: Mapped[int]
    new_release: Mapped[MyType] = mapped_column(SQLAlchemyEnum(MyType))


def init_db_session(connection_string: str) -> Type[sessionmaker]:
    try:
        engine = create_engine(connection_string, echo=False)
        Session = sessionmaker(bind=engine)
        return Session
    except SQLAlchemyError:
        raise


def pack_data_into_db(Session: Type[sessionmaker], catalog: list[dict[str, str | int | MyType]]) -> None:
    Catalog.__table___.create(checkfirst=True)
    with Session() as session:
        for item in catalog:
            bd_item = Catalog(
                title=item["title"],
                image_url=item["image_url"],
                fix_price=item["fix_price"],
                price=item["price"],
                new_release=item["new_release"]
            )
            session.add(bd_item)
        session.commit()
