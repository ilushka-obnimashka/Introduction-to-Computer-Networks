"""
Этот модуль определяет функции для взаимодействия
с базой данных PostgreSQL, включая создание сессий, таблиц и сохранение данных.
"""
from datetime import datetime
from typing import Type, List, Dict, Union

from sqlalchemy import String, Integer, Column
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy.orm import sessionmaker


class Base(DeclarativeBase):
    pass


class Catalog(Base):
    __abstract__ = True
    id: Mapped[int] = Column(Integer, primary_key=True)
    title: Mapped[str] = Column(String)
    image_url: Mapped[str] = Column(String)
    fix_price: Mapped[str] = Column(String)
    price: Mapped[int] = Column(Integer)
    new_release: Mapped[str] = Column(String)


def init_db_session(connection_string: str) -> tuple[Type[sessionmaker], Engine]:
    """
    Инициализирует сессию базы данных SQLAlchemy и возвращает её вместе с движком.
    Args:
        connection_string: Строка подключения к базе данных PostgreSQL.
    Returns:
        Кортеж, содержащий класс sessionmaker и объект Engine.
    Raises:
        SQLAlchemyError: Если не удается установить соединение с базой данных.
    """
    try:
        engine = create_engine(connection_string, echo=False)
        session = sessionmaker(bind=engine)
        return session, engine
    except SQLAlchemyError as e:
        raise SQLAlchemyError(f"Failed to initialize database session: {e}") from e


def pack_data_into_db(db_session: Type[sessionmaker], db_engine: Engine,
                      catalog: List[Dict[str, Union[str, int]]]) -> None:
    """
    Сохраняет данные из списка словарей в базу данных PostgreSQL.

    Args:
        db_session: Класс sessionmaker для создания сессий базы данных.
        db_engine: Объект Engine, представляющий соединение с базой данных.
        catalog: Список словарей, где каждый словарь представляет собой запись для таблицы Catalog.
    """

    class DynamicCatalog(Catalog):
        __tablename__ = f'{datetime.now().strftime("%d.%m.%y-%H:%M")}.catalogs'

    DynamicCatalog.__table__.create(db_engine)

    with db_session() as session:
        for item in catalog:
            bd_item = DynamicCatalog(
                title=item["title"],
                image_url=item["image_url"],
                fix_price=item["fix_price"],
                price=item["price"],
                new_release=item["new_release"]
            )
            session.add(bd_item)
        session.commit()
