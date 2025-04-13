import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.database import init_db_session, pack_data_into_db, Base
from src.parsing import init_browser, select_city, find_target_page, parse_catalog

app = FastAPI()


@app.post(
    "/parse",
    tags=["Парсинг 🕷️"],
    summary="Запуск парсинга 🚀",
    response_description="Сообщение о завершении парсинга ✅",
    description="""Запускает парсинг каталога продуктов с сайта La-Rose для указанного города. 🛒
        Сохраняет результаты в базу данных PostgreSQL.

        - **city**: Город для парсинга (Москва, Барнаул, Новосибирск).
        - **user**: Имя пользователя PostgreSQL.
        - **password**: Пароль пользователя PostgreSQL.
        - **host**: Хост PostgreSQL сервера.
        - **port**: Порт PostgreSQL сервера.
        - **dbname**: Имя базы данных PostgreSQL.
        """
)
def parse(
        city: str = os.environ.get("CITY"),
        user: str = os.environ.get("DB_USER"),
        password: str = os.environ.get("DB_PASSWORD"),
        host: str = os.environ.get("DB_HOST"),
        port: str = os.environ.get("DB_PORT"),
        dbname: str = os.environ.get("DB_NAME"),
) -> dict:
    if city not in ["Москва", "Барнаул", "Новосибирск"]:
        raise ValueError(
            f'Недопустимый город: "{city}". Допустимые города: Москва, Барнаул, Новосибирск.'
        )

    driver = init_browser()
    driver.get("https://la-rose.ru/")
    select_city(driver, city)
    find_target_page(driver)
    catalog = parse_catalog(driver)

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    db_session, db_engine = init_db_session(connection_string)
    pack_data_into_db(db_session, db_engine, catalog)
    driver.quit()
    return {
        "message": f"Парсинг завершен. В базу данных добавлено {len(catalog)} позиций."
    }


@app.get(
    "/get-catalog",
    tags=["Каталог 📂"],
    summary="Получение информации об ассортименте цветочного магазина la-rose в JSON 📄",
    description="""Возвращает JSON-представление каталога товаров из указанной таблицы базы данных.
    
    - **table_name**: Имя таблицы для запроса данных. По умолчанию нет значения.
    - **user**: Имя пользователя PostgreSQL.
    - **password**: Пароль пользователя PostgreSQL.
    - **host**: Хост PostgreSQL сервера.
    - **port**: Порт PostgreSQL сервера.
    - **dbname**: Имя базы данных PostgreSQL.
    """
)
def get_catalog_json(
        table_name: str,
        user: str = os.environ.get("DB_USER"),
        password: str = os.environ.get("DB_PASSWORD"),
        host: str = os.environ.get("DB_HOST"),
        port: str = os.environ.get("DB_PORT"),
        dbname: str = os.environ.get("DB_NAME"),
) -> list[dict[str, str | int]]:
    if table_name is None or table_name.strip() == "":
        error_message = f"Table name is required, but got: {table_name}"
        raise HTTPException(status_code=400, detail=error_message)

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    db_session, db_engine = init_db_session(connection_string)

    Base.metadata.reflect(db_engine)

    class DynamicCatalog(Base):
        try:
            __table__ = Base.metadata.tables[table_name]
        except Exception as e:
            error_message = (
                f"Table '{table_name}' does not exist or could not be loaded: {str(e)}"
            )
            raise HTTPException(status_code=404, detail=error_message) from e

    with db_session() as session:
        try:
            query = session.query(DynamicCatalog).all()
            return [
                {"id": item.id,
                 "title": item.title,
                 "image_url": item.image_url,
                 "fix_price": item.fix_price,
                 "price": item.price,
                 "new_release": item.new_release,
                 } for item in query]

        except SQLAlchemyError as e:
            error_message = f"Failed to access table '{table_name}': {str(e)}"
            raise HTTPException(status_code=500, detail=error_message) from e


if __name__ == "__main__":
    load_dotenv("src/.env")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
