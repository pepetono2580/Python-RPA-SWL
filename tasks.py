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
from Scrapper import Scrapper
import logging

browser = Selenium()

parameters = {
    "search_phrase": "donald trump",
    "news_category": "Story",
    "n_of_months": 1
}

open_searchbox_css = "css:button[data-element='search-button']"
search_button_css = "css:button[data-element='search-submit-button']"
search_box_name = "name:q"
search_icon_link = "#icon-magnify"
see_all_class = "class:see-all-text"
labels_class = "class:checkbox-input-label"
sort_class = "class:select-input"
web_address = "https://www.latimes.com/"
news_class = "class:promo-wrapper"
image_news_class = "image"
prev_container_class = "class:search-results-module-results-menu"
option_dropdown_value = "1"
next_page_class = "class:search-results-module-next-page"
output_folder = "output"
timestamp_class = "promo-timestamp"
timestamp_attribute_class = "data-timestamp"
title_class = "promo-title"
description_class = "promo-description"
image_class = "image"
image_src_attribute = "src"

sudden_popup_id = "id:modality-466828739218"
close_sudden_popup_locator = "class:met-flyout-close"
 
    
def main():
    logging.basicConfig(filename="webscrapping.log", level=logging.INFO)
    logging.info("Assigning workitems")
    
    s_phrase = parameters["search_phrase"]
    n_category = parameters["news_category"]
    n_of_months = parameters["n_of_months"]
    scrapper = Scrapper(s_phrase, n_category, n_of_months, web_address)
    
    try:
        scrapper.open_chrome_browser(web_address)
        scrapper.search_phrase(s_phrase, open_searchbox_css, search_box_name, search_button_css)
        scrapper.select_category(n_category, see_all_class, labels_class)
        prev_container = scrapper.sort_by_newest(news_class, sort_class, option_dropdown_value)
        get_news_list = scrapper.get_sorted_news_elements(prev_container, sudden_popup_id, news_class, 
                                                          next_page_class, 
                                                          close_sudden_popup_locator, 
                                                          timestamp_class, 
                                                          timestamp_attribute_class, 
                                                          title_class, description_class, 
                                                          image_class, image_src_attribute)
        
        for news in get_news_list:
            print(news)
        
        scrapper.write_news_to_Excel(get_news_list, output_folder)
        scrapper.iterate_by_news(get_news_list)
        
        
    except (SeleniumExceptions.ElementNotInteractableException, SeleniumExceptions.TimeoutException)  as exception:
        logging.info(f"{time.time()}    Failed at main due to:  {exception}")
        
    
    finally:
        scrapper.close_browser()
    
         
if __name__ == "__main__":
    
    main()
    