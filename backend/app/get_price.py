from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import re
from datetime import datetime
from pytz import timezone


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
        money, now_time = get_price(articul)
        money = pick_right_numbers(remove_spaces(money))
        return money, now_time.strftime(fmt)
    except Exception as e:
        zone = 'Europe/Moscow'
        now_time = datetime.now(timezone(zone))
        return e, now_time.strftime(fmt)


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
    price: WebElement = browser.find_element(By.CLASS_NAME, 'price-block__final-price')
    now_time = datetime.now(timezone(zone))
    zone = 'Europe/Moscow'

    txt = price.get_attribute("innerText")  

    browser.quit()
            
    return txt, now_time

    

print(get_price_high())