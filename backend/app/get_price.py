from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import re



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

    try:
        money = pick_right_numbers(remove_spaces(get_price(articul)))
        return money
    except Exception as e:
        return e


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
    browser.get(url) 
    price: WebElement = None
    while not price:
        try:    
            price = browser.find_element(By.CLASS_NAME, 'price-block__final-price') 
        except:
            continue

    txt = price.get_attribute("innerText")  

    browser.quit()
            
    return txt

    

print(get_price_high())