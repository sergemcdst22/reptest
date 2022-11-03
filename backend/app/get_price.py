from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import re
from datetime import datetime
from pytz import timezone
from time import sleep

def remove_spaces(s: str):
    return ''.join(s.split())

def pick_right_numbers(old_n):
    if old_n is None:
        return None
    else:
        digits = re.match("([0-9]*)",old_n).groups()[0]
        if digits.isdigit():
            return int(digits)
        else:
            return None

def get_price_high(articul=74249377):
    fmt = "%Y-%m-%d %H:%M:%S %Z%z"
    
    try:
        money, now_time, name = get_price(articul)
        if money == 0:
            return "Нет в наличии", now_time.strftime(fmt), name
        if money == -1:
            return "Товара с таким артикулом нет в базе (или ошибка загрузки, для проверки повторите запрос)", now_time.strftime(fmt), name
        money = pick_right_numbers(remove_spaces(money))
        return money, now_time.strftime(fmt), name
    except Exception as e:
        zone = 'Europe/Moscow'
        now_time = datetime.now(timezone(zone))
        return e, now_time.strftime(fmt), '?'


def get_price(articul=74249377):
    url = f'https://www.wildberries.ru/catalog/{articul}/detail.aspx'
 
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')        
    browser = webdriver.Chrome(options=options) 
    browser.implicitly_wait(2)
    browser.get(url)    
    zone = 'Europe/Moscow'
    soldout = None
    try:
        soldout = browser.find_element(By.CLASS_NAME, 'sold-out-product__text')
        names = browser.find_elements(By.TAG_NAME, 'h1')
        name = ' '.join([n.get_attribute("innerText") for n in names])
        span = browser.find_element(By.XPATH, '//span[@class="hide-mobile"]')
        name = span.get_attribute("innerText") + "/" + name
    except: ...
    if soldout:
        return 0, datetime.now(timezone(zone)), name
    price = None
    i = 0
    while not price and i < 5:
        try:
            price: WebElement = browser.find_element(By.CLASS_NAME, 'price-block__final-price')
        except:
            ...
        if not price:
            sleep(5)
            i += 1
    if not price:
        return -1, datetime.now(timezone(zone)), '?'
    now_time = datetime.now(timezone(zone))

    txt = price.get_attribute("innerText")
    names = browser.find_elements(By.TAG_NAME, 'h1')
    name = ' '.join([n.get_attribute("innerText") for n in names])
    span = browser.find_element(By.XPATH, '//span[@class="hide-mobile"]')
    name = span.get_attribute("innerText") + "/" + name

    browser.quit()
            
    return txt, now_time, name