from RPA.Browser.Selenium import Selenium
import copy
import selenium.common.exceptions as SeleniumExceptions
from datetime import datetime
import re
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from openpyxl import Workbook
import requests
from urllib.parse import urlparse, parse_qs
import os

browser = Selenium()

parameters = {
    "search_phrase": "donald trump",
    "news_category": "Story",
    "n_of_months": 1
}

open_searchbox_css = "button[data-element='search-button']"
search_button_css = "button[data-element='search-submit-button']"
search_box_name = "q"
search_icon_link = "#icon-magnify"
see_all_class = "see-all-text"
labels_class = "checkbox-input-label"
sort_class = "select-input"
web_address = "https://www.latimes.com/"
news_class = "promo-wrapper"
image_news_class = "image"
prev_container_class = "class:search-results-module-results-menu"
option_dropdown_value = "1"
next_page_class = "class:search-results-module-next-page"

sudden_popup_id = "id:modality-466828739218"


def open_browser(address: str):
    browser.open_chrome_browser(address, maximized=True)
    # browser.maximize_browser_window()


def search_phrase(phrase: str):
    browser.click_element(f"css:{open_searchbox_css}")
    browser.input_text_when_element_is_visible(f"name:{search_box_name}", phrase)
    browser.click_element(f"css:{search_button_css}")


def select_category(category: str):
    # browser.click_element("class:SearchFilter-content")
    see_all = browser.find_elements(f"class:{see_all_class}")
    see_all[1].click()
    labels = browser.find_elements(f"class:{labels_class}")
    for label in labels:
        
        if category in label.text:
            checkbox = label.find_element("xpath", ".//preceding-sibling::input[@type='checkbox']") 
            checkbox.click()
            break

         
def sort_by_newest():
    
    previous_news = browser.find_elements(f"class:{news_class}")
    dropdown = browser.find_element(f"class:{sort_class}")
    try:
        dropdown.click()
    except SeleniumExceptions.StaleElementReferenceException:
        dropdown = browser.find_element(f"class:{sort_class}")
        
    # previous_container = browser.find_element(prev_container_class).text
    browser.wait_until_element_is_enabled(f"class:{sort_class}", timeout=5)
    option_selector = f"class:{sort_class} option[value='{option_dropdown_value}']"
    browser.click_element(option_selector)
    
    time.sleep(3)
    
    return previous_news
    

def compare_containers(locator, timeout=10):
    
    initial_content = browser.find_elements(locator)
    for _ in range(timeout):
        browser.driver.implicitly_wait(1)
        current_content = browser.find_elements(locator)
        if current_content != initial_content:
            return True
    return False


def get_sibling_with_class(element, sibling_class, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            parent = element.find_element(By.XPATH, '..')
            sibling = parent.find_element(By.XPATH, f".//*[contains(@class, '{sibling_class}')]")
            return sibling
        except (SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException):
            retries += 1
            WebDriverWait(browser.driver, 1).until(lambda driver: False)  # Small delay to wait before retrying
    return None


def get_sorted_news_elements(news_container:list):
    news_list = []
    found_timestamp = False
    search_phr:str = parameters["search_phrase"]
    date_value = parameters["n_of_months"]
    
    is_different = compare_containers(news_container)
    
    if not is_different:
        browser.driver.implicitly_wait(3)

    while not found_timestamp:
        
        articles = browser.find_elements(f"class:{news_class}")
        
        for index, news in enumerate(articles):
            
            current_news = news
            browser.assign_id_to_element(news, str(index))
            
            if browser.is_element_visible(sudden_popup_id):
                
                browser.click_element("class:met-flyout-close")
                browser.wait_until_element_is_not_visible(sudden_popup_id, timeout=5)
            
            try:
                timestamp = current_news.find_element(By.CLASS_NAME, "promo-timestamp")
            except SeleniumExceptions.StaleElementReferenceException:
                current_news:list = browser.find_elements(f"id:{index}")
                timestamp = current_news.index(0).find_element(By.CLASS_NAME, "promo-timestamp")
                         
            time_news = int(timestamp.get_attribute("data-timestamp")) / 1000
            
            if datetime.fromtimestamp(time_news).month < month_from_parameters(date_value):
                found_timestamp = True
                return news_list
            
            
            title = current_news.find_element(By.CLASS_NAME, "promo-title")
            str_title = title.text
            print(str_title)
            description = current_news.find_element(By.CLASS_NAME, "promo-description")
            str_desc = description.text
            try:
                image_url = current_news.find_element(By.CLASS_NAME, "image")
                image = image_url.get_attribute("src")
            except SeleniumExceptions.NoSuchElementException as exception:
                image = None
                
            title_has_money = contains_money(str_title)
            desc_has_money = contains_money(str_desc)
            count_title_search_phrase = str_title.lower().count(search_phr.lower()) 
            count_desc_search_phrase = str_desc.lower().count(search_phr.lower())
            
            has_money = compare_bools(title_has_money, desc_has_money)
            picture_filename = extract_image_name_from_URL(image)
            
            news_list.append({"title": str_title, 
                            "description": str_desc,
                            "timestamp": time_news, 
                            "image_url": image, 
                            "phrase_count": count_title_search_phrase + count_desc_search_phrase, 
                            "contains_money": has_money,
                            "picture_filename": picture_filename})
            
        try:
            browser.click_element(next_page_class)
        except SeleniumExceptions.ElementClickInterceptedException as exception:
            return news_list


def get_news(n_list):
    """ news_list = []
    browser.wait_until_page_contains_element(f"class:{news_class}")
    
    try:
        news_list = n_list
    except SeleniumExceptions.StaleElementReferenceException:
        news_list = n_list """
    
    for news in n_list:
        print(news)
    


def contains_money(text):
    pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|(\d+)\s?(dollars|USD)'
    
    match = re.search(pattern, text, re.IGNORECASE)
    
    return bool(match)


def compare_bools(title, description):
    if title and description:
        return True
    elif not title or not description:
        return False
    else:
        return False
    

def month_from_parameters(month:int):
    date = None
    match month:
        case 0 | 1:
            date = datetime.today().month
        case 2:
            date = datetime.today().month - 1
        case 3:
            date = datetime.today().month - 2
    
    return date


def write_news_to_Excel(news_list:list, output_folder):
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    temp_list = copy.deepcopy(news_list)
    
    for news in temp_list:
        del news["image_url"]
    
    workbook = Workbook()
    sheet = workbook.active
    
    header = list(temp_list[0].keys())
    sheet.append(header)
    
    for item in temp_list:
        sheet.append(list(item.values()))
        
    workbook.save(f"{output_folder}/news_list.xlsx")


def download_image(url, save_path):
    try:
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
    
    except requests.exceptions.RequestException as exception:
        print(exception)       


def iterate_by_news(news_list:list):
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    download_folder = os.path.join(base_dir, "output")
    
    for news in news_list:
        if not news["picture_filename"] or '.' not in news["picture_filename"]:
            news["picture_filename"] += ".jpg"
            
        save_path = os.path.join(download_folder, f"{news['picture_filename']}")
        download_image(news["image_url"], save_path)


def extract_image_name_from_URL(url:str):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    inner_url = query_params.get('url', [None])[0]
    
    if inner_url:
        return os.path.basename(urlparse(inner_url).path)
    else:
        return None


def main():
    open_browser(web_address)
    search_phrase(parameters["search_phrase"])
    select_category(parameters["news_category"])

    prev_container = sort_by_newest()

    get_news_list = get_sorted_news_elements(prev_container)
    get_news(get_news_list)
    write_news_to_Excel(get_news_list, "output")
    iterate_by_news(get_news_list)


if __name__ == "__main__":
    
    try:
        main()
    
    except SeleniumExceptions.ElementNotInteractableException as exception:
        print(exception)
        
    except SeleniumExceptions.TimeoutException as exception:
        print(exception)
        
    finally:
        browser.close_browser()