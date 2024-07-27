from RPA.Browser.Selenium import Selenium
import copy
import selenium.common.exceptions as SeleniumExceptions
from datetime import datetime
import re
from selenium.webdriver.common.by import By
from openpyxl import Workbook
import requests
from urllib.parse import urlparse, parse_qs
import os, glob
import time
import logging

class Scrapper:
    def __init__(self, search_phrase, news_category, n_of_months, site_url):
        self.s_phrase = search_phrase
        self.news_category = news_category
        self.n_of_months = n_of_months
        self.browser = Selenium()
        self.URL = site_url

    
    def clean_file_and_folder(self, output_path, logs_file):
        logging.info(f"{time.time()}    Clean file and folder ")
        try:
            files = glob.glob(f'{output_path}/.*')
            if os.path.isfile(logs_file):
                os.remove(logs_file)
            for file in files:
                os.remove(file)
        except Exception as e:
            logging.info(f"{time.time()}    Failed at cleaning file and folder: {e}")
            
        
        
    def open_chrome_browser(self, address: str):
        logging.info(f"{time.time()}    Open browser ")
        try:
            self.browser.open_chrome_browser(address, maximized=True)
        except Exception as e:
            logging.info(f"{time.time()}    Failed at opening Chrome browser: {e}")
    
    
    def search_phrase(self, phrase: str, open_searchbox_locator, input_text_locator, search_element_locator):
        logging.info(f"{time.time()}    Searching for input phrase")
        try:
            self.browser.click_element(open_searchbox_locator)
            self.browser.input_text_when_element_is_visible(input_text_locator, phrase)
            self.browser.click_element(search_element_locator)
        except (Exception, SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException) as e:
            logging.info(f"{time.time()}    Failed at searching input phrase due to: {e}")
    
    
    def select_category(self, category:str, see_all_locator:str, categories_labels_locator:str):
        logging.info(f"{time.time()}    Selecting category")
        try:
            see_all = self.browser.find_elements(see_all_locator)
            see_all[1].click()
            labels = self.browser.find_elements(categories_labels_locator)
            
            for label in labels:
                
                if category in label.text:
                    checkbox = label.find_element("xpath", ".//preceding-sibling::input[@type='checkbox']") 
                    checkbox.click()
                    break
            
        except (Exception, SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException) as e:
            logging.info(f"{time.time()}    Failed at selecting category due to: {e}")
    
    
    def sort_by_newest(self, previous_news_locator:str, dropdown_filtering_selector:str, option_dropdown_value:str):
        logging.info(f"{time.time()}    Sorting by newest")
        
        try:
            previous_news = self.browser.find_elements(previous_news_locator)
            dropdown = self.browser.find_element(dropdown_filtering_selector)
            
            try:
                dropdown.click()
            except SeleniumExceptions.StaleElementReferenceException:
                dropdown = self.browser.find_element(dropdown_filtering_selector)
                
            self.browser.wait_until_element_is_enabled(dropdown_filtering_selector, timeout=5)
            option_selector = f"{dropdown_filtering_selector} option[value='{option_dropdown_value}']"
            self.browser.click_element(option_selector)
            
            time.sleep(3)
            return previous_news
        
        except (Exception, SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException) as e:
            logging.info(f"{time.time()}    Failed at sorting by newest due to: {e}")
    
    
    def compare_containers(self, locator:str, timeout=10):
        logging.info(f"{time.time()}    Comparing containers")
        
        try:
            initial_content = self.browser.find_elements(locator)
            
            for _ in range(timeout):
                self.browser.driver.implicitly_wait(1)
                current_content = self.browser.find_elements(locator)
                
                if current_content != initial_content:
                    return True
            return False
        
        except (Exception, SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException) as e:
            logging.info(f"{time.time()}    Failed at comparing containers due to: {e}")
    
    
    def month_from_parameters(self, month:int):
        date = None
        match month:
            case 0 | 1:
                date = datetime.today().month
            case 2:
                date = datetime.today().month - 1
            case 3:
                date = datetime.today().month - 2
        
        return date
        
    def get_sorted_news_elements(self, news_container:list, sudden_popup_locator:str, news_locator:str, 
                                 next_page_locator:str, close_sudden_popup_locator:str, timestamp_class:str, 
                                 timestamp_attribute:str, title_class:str, description_class:str, image_class:str, image_src:str):
        logging.info(f"{time.time()}    Getting sorted news")
        news_list = []
        found_timestamp = False
        search_phr:str = self.s_phrase
        date_value = self.n_of_months
        
        try:
            is_different = self.compare_containers(news_container)
            
            if not is_different:
                self.browser.driver.implicitly_wait(3)

            while not found_timestamp:
                
                articles = self.browser.find_elements(news_locator)
                
                for index, news in enumerate(articles):
                    
                    current_news = news
                    self.browser.assign_id_to_element(news, str(index))
                    
                    if self.browser.is_element_visible(sudden_popup_locator):
                        
                        self.browser.click_element(close_sudden_popup_locator)
                        self.browser.wait_until_element_is_not_visible(sudden_popup_locator, timeout=5)
                    
                    try:
                        timestamp = current_news.find_element(By.CLASS_NAME, timestamp_class)
                    except SeleniumExceptions.StaleElementReferenceException:
                        current_news:list = self.browser.find_elements(f"id:{index}")
                        timestamp = current_news.index(0).find_element(By.CLASS_NAME, timestamp_class)
                                
                    time_news = int(timestamp.get_attribute(timestamp_attribute)) / 1000
                    
                    if datetime.fromtimestamp(time_news).month < self.month_from_parameters(date_value):
                        found_timestamp = True
                        return news_list
                    
                    
                    title = current_news.find_element(By.CLASS_NAME, title_class)
                    str_title = title.text
                    print(str_title)
                    description = current_news.find_element(By.CLASS_NAME, description_class)
                    str_desc = description.text
                    try:
                        image_url = current_news.find_element(By.CLASS_NAME, image_class)
                        image = image_url.get_attribute(image_src)
                    except SeleniumExceptions.NoSuchElementException as exception:
                        image = None
                        
                    title_has_money = self.contains_money(str_title)
                    desc_has_money = self.contains_money(str_desc)
                    count_title_search_phrase = str_title.lower().count(search_phr.lower()) 
                    count_desc_search_phrase = str_desc.lower().count(search_phr.lower())
                    
                    has_money = self.compare_bools(title_has_money, desc_has_money)
                    picture_filename = self.extract_image_name_from_URL(image)
                    
                    news_list.append({"title": str_title, 
                                    "description": str_desc,
                                    "timestamp": time_news, 
                                    "image_url": image, 
                                    "phrase_count": count_title_search_phrase + count_desc_search_phrase, 
                                    "contains_money": has_money,
                                    "picture_filename": picture_filename})
                    
                try:
                    self.browser.click_element(next_page_locator)
                except SeleniumExceptions.ElementClickInterceptedException as exception:
                    return news_list
        except (Exception, SeleniumExceptions.StaleElementReferenceException, SeleniumExceptions.NoSuchElementException, SeleniumExceptions.TimeoutException) as e:
            logging.info(f"{time.time()}    Failed at getting sorted news due to: {e}")
    
    
    def contains_money(self, text):
        pattern = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?|(\d+)\s?(dollars|USD)'
        
        match = re.search(pattern, text, re.IGNORECASE)
        
        return bool(match)
    
    
    def compare_bools(self, title, description):
        if title and description:
            return True
        elif not title or not description:
            return False
        else:
            return False
        
    
    def extract_image_name_from_URL(self, url:str):
        logging.info(f"{time.time()}    Extract image from URL")
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            
            inner_url = query_params.get('url', [None])[0]
            
            if inner_url:
                return os.path.basename(urlparse(inner_url).path)
            else:
                return None
        except Exception as e:
            logging.info(f"{time.time()}    Failed at extracting image from URL due to: {e}")

    
    def iterate_by_news(self, news_list:list):
        logging.info(f"{time.time()}    Extract image from URL")
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            download_folder = os.path.join(base_dir, "output")
            
            for news in news_list:
                if not news["picture_filename"] or '.' not in news["picture_filename"]:
                    news["picture_filename"] += ".jpg"
                    
                save_path = os.path.join(download_folder, f"{news['picture_filename']}")
                self.download_image(news["image_url"], save_path)
        except Exception as e:
            logging.info(f"{time.time()}    Failed at extracting image from URL due to: {e}")
            
    
    def download_image(self, url, save_path):
        logging.info(f"{time.time()}    Downloading image")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
        
        except requests.exceptions.RequestException as exception:
            logging.info(f"{time.time()}    Failed at downlading image due to: {exception}")
            
    
    def write_news_to_Excel(self, news_list:list, output_folder):
        logging.info(f"{time.time()}    Writing news to Excel")
        try:
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
        except Exception as e:
            logging.info(f"{time.time()}    Failed at writing news to Excel due to: {e}")
            
    
    
    def close_browser(self):
        self.browser.close_browser()