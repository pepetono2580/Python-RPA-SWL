from RPA.Browser.Selenium import Selenium
import copy
import selenium.common.exceptions as SeleniumExceptions
from datetime import datetime
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from openpyxl import Workbook
import requests
from urllib.parse import urlparse
import os

class Scraper:
    def __init__(self, search_phrase, news_category, n_of_months):
        self.search_phrase = search_phrase
        self.news_category = news_category
        self.n_of_months = n_of_months
        self.browser = Selenium()
        self.URL = "https://www.latimes.com/"
    
    
    def open_chrome_browser(self, address: str):
        self.browser.open_chrome_browser(address, maximized=True)
    
    
    def search_phrase(self, phrase: str, open_searchbox_locator, input_text_locator, search_element_locator):
        self.browser.click_element(open_searchbox_locator)
        self.browser.input_text_when_element_is_visible(input_text_locator, phrase)
        self.browser.click_element(search_element_locator)
    
    def select_category(self, category: str, see_all_locator, categories_labels_locator):
    
        see_all = self.browser.find_elements(see_all_locator)
        see_all[len(see_all) - 1].click()
        labels = self.browser.find_elements(categories_labels_locator)
        
        for label in labels:
            
            if category in label.text:
                checkbox = label.find_element("xpath", ".//preceding-sibling::input[@type='checkbox']") 
                checkbox.click()
                break
    
    def sort_by_newest(self, previous_news_locator:str, dropdown_filtering_selector:str, option_dropdown_value:str):
    
        previous_news = self.browser.find_elements(previous_news_locator)
        dropdown = self.browser.find_element(dropdown_filtering_selector)
        
        try:
            dropdown.click()
        except SeleniumExceptions.StaleElementReferenceException:
            dropdown = self.browser.find_element(dropdown_filtering_selector)
            
        self.browser.wait_until_element_is_enabled(dropdown_filtering_selector, timeout=5)
        option_selector = f"{dropdown_filtering_selector} option[value='{option_dropdown_value}']"
        self.browser.click_element(option_selector)
        
        return previous_news
    
    
    def compare_containers(self, locator, timeout=10):
    
        initial_content = self.browser.find_elements(locator)
        
        for _ in range(timeout):
            self.browser.driver.implicitly_wait(1)
            current_content = self.browser.find_elements(locator)
            
            if current_content != initial_content:
                return True
        return False
    