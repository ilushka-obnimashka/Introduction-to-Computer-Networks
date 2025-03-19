import click
from enum import Enum
from src.parsing import init_browser, select_city, find_target_page, parse_catalog, pack_data_into_csv
from src.database import init_db_session, pack_data_into_db

class MyType(Enum):
    YES = "yes"
    NO = "no"

@click.command()
@click.option(
    '--city',
    default='Новосибирск',
    type=str,
    help='Указывает город для парсинга сайта "la-rose.ru/" и получения текущего ассортимента цветов.'
)
@click.option(
    '--user',
    default='postgres',
    type=str,
    help='Имя пользователя для подключения к PostgreSQL.'
)
@click.option(
    '--password',
    default='6419',
    type=str,
    help='Пароль для подключения к PostgreSQL.'
)
@click.option(
    '--host',
    default='localhost',
    type=str,
    help='Хост для подключения к PostgreSQL.'
)
@click.option(
    '--port',
    default='5432',
    type=str,
    help='Порт для подключения к PostgreSQL.'
)
@click.option(
    '--dbname',
    default='la-rose_product_catalog',
    type=str,
    help='Название базы данных для подключения к PostgreSQL.'
)

def main(city, user, password, host, port, dbname) -> None:
    """
    Основная функция для запуска скрипта парсинга.
    Args:
        kwargs : Аргументы командной строки.
    """

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
    db_session = init_db_session(connection_string)
    pack_data_into_db(db_session, catalog)
    driver.quit()


if __name__ == '__main__':
    main()
