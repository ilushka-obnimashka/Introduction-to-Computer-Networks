import click
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def init_browser():
    """
    Инициализирует браузер Chrome в режиме без графического интерфейса.
    returns:
        webdriver.Chrome: Объект драйвера для управления браузером.
    """
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(service=service, options=options)

def select_city(driver, city_name: str):
    """
    Выбирает указанный город через всплывающее окно при запуске сайта.
    Args:
        driver (webdriver.Chrome): Объект драйвера браузера.

        city_name: Название города для выбора
    """
    city_confirmation_message = driver.find_element(
        By.CSS_SELECTOR, '#main > div.confirm_region > div.title'
    )
    text = city_confirmation_message.text

    if city_name in text:
        driver.find_element(
            By.CSS_SELECTOR,
            '#main > div.confirm_region > div.buttons > span.btn.btn-default.aprove'
        ).click()
    elif city_name not in text and city_name == 'Москва':
        driver.find_element(
            By.CSS_SELECTOR,
            '#main > div.confirm_region > div.buttons > span.btn.btn-default.white.js_city_change'
        ).click()
        driver.find_element(
            By.CSS_SELECTOR,
            '#main > div.city_chooser_small_frame.jqmWindow.popup.jqm-init.show > div > '
            'div.popup_regions > div.items.only_city > div > div > div.item.current'
        ).click()
    else:
        driver.find_element(
            By.CSS_SELECTOR,
            '#main > div.confirm_region > div.buttons > span.btn.btn-default.white.js_city_change'
        ).click()
        driver.find_element(By.XPATH, f'//a[text()="{city_name}"]').click()

def find_target_page(driver):
    """
    Находит целевую страницу для парсинга: menu -> каталог -> букеты.
    Args:
        driver (webdriver.Chrome): Объект драйвера браузера.
    """
    driver.find_element(
        By.CSS_SELECTOR, '#new-tmp-header-menu > div.mobileheader-v1 > div > span'
    ).click()
    driver.find_element(
        By.CSS_SELECTOR, '#new-mobilemenu > div > div > ul > li:nth-child(1) > a > span'
    ).click()
    driver.find_element(
        By.CSS_SELECTOR,
        "#bx_1847241719_80 > table > tbody > tr > td.section_info > ul > li.name > a > span"
    ).click()

def parse_catalog(driver) -> list[dict[str, str]] :
    """
    Парсит каталог букетов и собирает данные в список словарей.
    Args:
        driver (webdriver.Chrome): Объект драйвера браузера.
    Returns:
        Список словарей с данными о букетах.
    """
    catalog = []

    while True:
        products = driver.find_elements(By.CSS_SELECTOR, 'div.item_block.col-3.col-md-4.col-sm-6.col-xs-6.col-small-12')

        for product in products:
            title = product.find_element(By.XPATH,
                                         './/img[@src and @data-hover-image and @alt and @title]').get_attribute('title')
            image_url = product.find_element(By.XPATH,
                                              './/img[@src and @data-hover-image and @alt and @title]').get_attribute('src')

            try:
                price = product.find_element(By.CSS_SELECTOR,
                                              'div.price_matrix_block div.price_matrix_wrapper div.price[data-currency]'
                                              '[data-value]').get_attribute('data-value')
                fix_price = 'yes'
            except NoSuchElementException:
                fix_price = 'no'
                price = product.find_element(By.CSS_SELECTOR, 'div.price.flex.mob-price').text
                price = price.replace(' ', '').replace('₽', '')

            try:
                new_release = product.find_element(By.CSS_SELECTOR, 'div.sticker_novinka').text
            except NoSuchElementException:
                new_release = 'no'

            catalog.append({
                'title': title,
                'image_url': image_url,
                'fix_price': fix_price,
                'price': int(price),
                'new_release': new_release
            })

        try:
            show_more_button = driver.find_element(By.CSS_SELECTOR,
                                                   '#right_block_ajax > div.inner_wrapper > div.ajax_load.block >'
                                                   ' div.bottom_nav.block > div.ajax_load_btn')
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", show_more_button)
            show_more_button.click()
        except NoSuchElementException:
            break

    return catalog

def pack_data_into_csv(filename: str, data: list[dict[str, str]]) -> None:
    """
    Сохраняет данные в CSV файл.
    Args:
        filename (str): Имя выходного CSV файла.
        data (list[dict]): Данные для записи в файл.
    """
    parsed_df = pd.DataFrame(data)
    parsed_df.columns = data[0].keys()

    try:
        parsed_df.to_csv(filename, index=False)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

@click.command()
@click.option(
    '--city',
    default='Новосибирск',
    type=str,
    help='Указывает город для парсинга сайта "la-rose.ru/" и получения текущего ассортимента цветов.'
)
@click.option(
    '--output',
    default='output.csv',
    type=str,
    help='Указывает имя выходного файла с результатами работы скрипта.'
)
def main(**kwargs) -> None:
    """
    Основная функция для запуска скрипта парсинга.
    Args:
        kwargs : Аргументы командной строки.
    """
    target_city = kwargs['city']
    if target_city not in ['Москва', 'Барнаул', 'Новосибирск']:
        raise ValueError(
            f'Недопустимый город: "{target_city}". Допустимые города: Москва, Барнаул, Новосибирск.'
        )

    driver = init_browser()
    driver.get('https://la-rose.ru/')
    select_city(driver, target_city)
    find_target_page(driver)
    catalog = parse_catalog(driver)
    pack_data_into_csv(kwargs['output'], catalog)
    driver.quit()

if __name__ == '__main__':
    main()
