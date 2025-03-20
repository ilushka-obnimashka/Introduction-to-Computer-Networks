import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from src.database import init_db_session, pack_data_into_db, Base
from src.parsing import init_browser, select_city, find_target_page, parse_catalog

app = FastAPI()


@app.post("/parse",
          tags=["Парсинг 🕷️"],
          summary="Запуск парсинга 🚀",
          response_description="Сообщение о завершении парсинга ✅",
          description="""Запускает парсинг каталога продуктов с сайта La-Rose для указанного города. 🛒
              Сохраняет результаты в базу данных PostgreSQL.

              - **city**: Город для парсинга (Москва, Барнаул, Новосибирск). По умолчанию Новосибирск.
              - **user**: Имя пользователя PostgreSQL. По умолчанию postgres.
              - **password**: Пароль пользователя PostgreSQL. По умолчанию 6419.
              - **host**: Хост PostgreSQL сервера. По умолчанию localhost.
              - **port**: Порт PostgreSQL сервера. По умолчанию 5432.
              - **dbname**: Имя базы данных PostgreSQL. По умолчанию la-rose_product_catalog.
              """)
def parse(city: str = "Новосибирск",
          user: str = "postgres",
          password: str = "6419",
          host: str = "localhost",
          port: str = "5432",
          dbname: str = "la-rose_product_catalog") -> None:
    if city not in ['Москва', 'Барнаул', 'Новосибирск']:
        raise ValueError(
            f'Недопустимый город: "{city}". Допустимые города: Москва, Барнаул, Новосибирск.'
        )

    driver = init_browser()
    driver.get('https://la-rose.ru/')
    select_city(driver, city)
    find_target_page(driver)
    catalog = parse_catalog(driver)

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    db_session, db_engine = init_db_session(connection_string)
    pack_data_into_db(db_session, db_engine, catalog)
    driver.quit()
    return {"message": "Парсинг завершен и данные сохранены в базу данных"}


@app.get(
    "/get-catalog",
    tags=["Каталог 📂"],
    summary="Получение информации об ассортименте цветочного магазина la-rose в JSON 📄",
    description="""Возвращает JSON-представление каталога товаров из указанной таблицы базы данных.
    
    - **user**: Имя пользователя PostgreSQL.
    - **password**: Пароль пользователя PostgreSQL.
    - **host**: Хост PostgreSQL сервера.
    - **port**: Порт PostgreSQL сервера.
    - **dbname**: Имя базы данных PostgreSQL.
    - **table_name**: Имя таблицы для запроса данных.
    """
)
def get_catalog_json(
        user: str = "postgres",
        password: str = "6419",
        host: str = "localhost",
        port: str = "5432",
        dbname: str = "la-rose_product_catalog", table_name: str = '25.03.20-07:48.catalogs'):
    if table_name is None or table_name.strip() == '':
        error_message = f"Table name is required, but got: {table_name}"
        raise HTTPException(status_code=400, detail=error_message)

    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    db_session, db_engine = init_db_session(connection_string)

    Base.metadata.reflect(db_engine)

    class DynamicCatalog(Base):
        try:
            __table__ = Base.metadata.tables[table_name]
        except Exception as e:
            error_message = f"Table '{table_name}' does not exist or could not be loaded: {str(e)}"
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


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
