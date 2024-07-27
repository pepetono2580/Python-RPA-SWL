import selenium.common.exceptions as SeleniumExceptions
import time
from Scrapper import Scrapper
import logging
from robocorp import vault
from robocorp.tasks import task
from RPA.Robocorp.WorkItems import WorkItems
import constants
 
@task    
def main():
    
    workitems = WorkItems()
    
    web_address = "www.latimes.com/"
    #wb_address = vault.get_secret("URL_from_website")
    #web_address = wb_address["URL"]
    
    workitems.get_input_work_item()
    variable = workitems.get_work_item_payload()
    
    s_phrase = variable["search_phrase"]
    n_category = variable["news_category"]
    n_of_months = variable["n_of_months"]
    scrapper = Scrapper(s_phrase, n_category, n_of_months, web_address)
    logging.basicConfig(filename=constants.LOG_FILENAME, level=logging.INFO)
    
    try:
        scrapper.clean_file_and_folder(constants.OUTPUT_FOLDER, constants.LOG_FILENAME)
        
        scrapper.open_chrome_browser(web_address)
        scrapper.search_phrase(s_phrase, constants.OPEN_SEARCHBOX_CSS, constants.SEARCH_BOX_NAME, constants.SEARCH_BUTTON_CSS)
        scrapper.select_category(n_category, constants.SEE_ALL_CLASSES, constants.LABELS_CLASS)
        prev_container = scrapper.sort_by_newest(constants.NEWS_CLASS, constants.SORT_CLASS, constants.OPTION_DROPDOWN_VALUE)
        get_news_list = scrapper.get_sorted_news_elements(prev_container, 
                                                          constants.SUDDEN_POPUP_ID, 
                                                          constants.NEWS_CLASS, 
                                                          constants.NEXT_PAGE_CLASS, 
                                                          constants.CLOSE_SUDDEN_POPUP_LOCATOR, 
                                                          constants.TIMESTAMP_CLASS, 
                                                          constants.TIMESTAMP_ATTRIBUTE_CLASS, 
                                                          constants.TITLE_CLASS, 
                                                          constants.DESCRIPTION_CLASS, 
                                                          constants.IMAGE_CLASS, 
                                                          constants.IMAGE_SRC_ATTRIBUTE)
        
        scrapper.write_news_to_Excel(get_news_list, constants.OUTPUT_FOLDER)
        scrapper.iterate_by_news(get_news_list)
        
        
    except (SeleniumExceptions.ElementNotInteractableException, SeleniumExceptions.TimeoutException)  as exception:
        logging.info(f"{time.time()}    Failed at main due to:  {exception}")
        
    
    finally:
        scrapper.close_browser()
    
    