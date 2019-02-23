import logging
from selenium import webdriver
from constants import local_paths

def start():
    logging.info('\nstarting the driver')
    driver = webdriver.PhantomJS(executable_path=local_paths.phantomjs_path)
    ## necessary for elements to be located
    driver.set_window_size(1124, 850)
    return driver