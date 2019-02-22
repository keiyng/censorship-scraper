# encoding: utf-8
import logging
import argparse
import threading
from queue import Queue
import time
import sys
import re
import os
import urllib
from connections import mysql_database
from constants import element_selector, local_path
from selenium import webdriver

EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)

def get_page(search_term, queue):

   get_success = False
   get_failure = 0

   try:
       search_term = search_term.encode('utf-8')
   except UnicodeError:
       sys.exit('cannot encode search term to utf-8.')

   quoted_search_term = urllib.parse.quote(search_term)

   while get_success is False and get_failure < 3:

       try:
           logging.info('\nstarting the driver')
           driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
           ## necessary for elements to be located
           driver.set_window_size(1124, 850)
           logging.info('\ngetting the page')
           driver.get('http://s.weibo.com/weibo/{}&Refer=STopic_box'.format(quoted_search_term))
           get_success = True
       except Exception as e:
           logging.info('\nAn error occured trying to visit the page')
           get_success = False
           get_failure += 1
           time.sleep(5)
       else:
          get_success, get_failure = expand_content(driver, get_success, get_failure)

   if get_success is True:
       data = scrape(driver)
       queue.put(data)
       logging.info('\nscraping done')

   return


def expand_content(driver, get_success, get_failure):

   expand_success = False
   expand_failure = 0
   
   while expand_success is False and expand_failure < 2:
       try:
           expand = driver.find_elements_by_partial_link_text(element_selector.EXPAND_TEXT_SELECTOR)
           clicked = 0
           logging.info('\nexpanding elements')
           for ele in expand:
               ele.click()
               ## allow time for the click to complete
               time.sleep(5)
               clicked += 1

       except Exception as e:
           logging.info('\nAn error occured trying to expand element')
           expand_success = False
           expand_failure += 1
           time.sleep(5)

       else:
           collapse = driver.find_elements_by_partial_link_text(element_selector.COLLAPSE_TEXT_SELECTOR)

           if clicked != len(collapse):
               driver.quit()
               get_success = False
               get_failure += 1
               logging.info('\nno. of expand and collapse do not match. Start again...')
               time.sleep(10)
               break
           else:
               expand_success = True

   return get_success, get_failure


def scrape(driver):

   full_content_div = driver.find_elements_by_css_selector(element_selector.FULL_CONTENT_SELECTOR)

   content = []
   url = []
   mid = []

   for ele in full_content_div:
       if (not ele.find_elements_by_css_selector(element_selector.MEDIA_SELECTOR)) and (not ele.find_elements_by_css_selector(element_selector.REBLOG_SELECTOR)) and (not ele.find_elements_by_css_selector(element_selector.REBLOG_SELECTOR_2)) and (not ele.find_elements_by_partial_link_text(element_selector.LINK_SELECTOR)) and (not ele.find_elements_by_css_selector(element_selector.VIDEO_SELECTOR)):

           if ele.find_elements_by_css_selector(element_selector.CONTENT_SELECTOR) and \
           ele.find_element_by_css_selector(element_selector.CONTENT_SELECTOR).text != '':
               content.append(ele.find_element_by_css_selector(element_selector.CONTENT_SELECTOR).text)
               mid.append(ele.get_attribute("mid"))
           if ele.find_elements_by_css_selector(element_selector.EXPANDED_CONTENT_SELECTOR) and \
           ele.find_element_by_css_selector(element_selector.EXPANDED_CONTENT_SELECTOR).text != '':
               content.append(ele.find_element_by_css_selector(element_selector.EXPANDED_CONTENT_SELECTOR).text)
               mid.append(ele.get_attribute("mid"))
           if ele.find_elements_by_css_selector(element_selector.URL_SELECTOR):
               url.append(ele.find_element_by_css_selector(element_selector.URL_SELECTOR))


   url = [ele.get_attribute("href") for ele in url]

   if len(url) != len(content):
       logging.info('\nurl len:' + str(len(url)))
       logging.info('\ncontent len:' + str(len(content)))
       driver.quit()
       sys.exit('\nscraped content not aligning')

   logging.info('\nno. of posts scraped: {}'.format(str(len(content))))
   simplified_url = [u[0:u.find('?')] for u in url]
   uid = [u.split('/')[-2] for u in simplified_url]
   pid = [u.split('/')[-1] for u in simplified_url]

   cleaned_content = []

   for c in content:
       c = re.sub(r'\n+', ' ', c)
       c = re.sub(EMOJI, ' ', c)
       c= re.sub(',', '，', c)
       cleaned_content.append(c)


   driver.quit()

   data = {'content': cleaned_content, 'url': simplified_url, 'uid': uid, 'pid': pid, 'mid': mid}

   return data


def save_to_db(table, queue):
   saved = 0
   skipped = 0

   conn, cur = mysql_database.connect()

   cur.execute('SELECT url from {}'.format(table))
   ## turn tuple of tuples into list of strings
   exisiting_urls = [''.join(ele) for urls in list(cur.fetchall()) for ele in urls]

   while not queue.empty():
       data = queue.get()

       for i in range(len(data["content"])):
           if data["url"][i] not in exisiting_urls:

               try:
                   cur.execute('''INSERT INTO {} (content, url, uid, pid, mid, pubdate, tested, testdate, status)
                                   VALUES (%s, %s, %s, %s, %s, CURDATE(), DEFAULT, DEFAULT, DEFAULT)'''.format(table), \
                                   (data["content"][i], data["url"][i], data["uid"][i], data["pid"][i], data["mid"][i]))
                   logging.info('\nsaved pid: {}'.format(data["pid"][i]))

                   saved += 1
                   cur.connection.commit()
               except Exception as e:
                   logging.info('\nunable to insert pid {} ... into table.'.format(data["pid"][i]))
                   continue
           else:
               skipped += 1

   logging.info('\nsaved: {}; skipped: {}'.format(saved, skipped))

   cur.execute('SELECT COUNT(*) FROM {}'.format(table))
   no_of_rows = str(cur.fetchone()[0])
   logging.info('\nno. of rows in database: {}'.format(no_of_rows))

   mysql_database.disconnect(conn, cur)

   return



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(threadName)s:%(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument('terms', nargs='+')
    parser.add_argument('table', nargs=1)

    args = vars(parser.parse_args())
    terms = args["terms"]
    table = args["table"][0]

    queue = Queue()

    try:
        threads = [threading.Thread(target=get_page, args=(terms[i], queue)) for i in range(len(terms))]
    except Exception as e:
        logging.info('\nunable to start scraping threads.')
        driver.quit()

    for thread in threads:
        thread.start()

    # wait for all threads to complete.
    for thread in threads:
        thread.join()

    try:
        threading.Thread(target=save_to_db, args=(table, queue)).start()
    except Exception as e:
        logging.info('\nunable to start database thread.')
        driver.quit()
