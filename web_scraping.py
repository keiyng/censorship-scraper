# encoding: utf-8
import logging
import argparse
import threading
from queue import Queue
import time
import sys
import re
import urllib
from connections import mysql_database, phantomjs
from constants import element_selectors as select, filter_words


def find_element(obj, find_by, selector):
    if find_by == 'css':
        return obj.find_elements_by_css_selector(selector)
    elif find_by == 'css singular':
        return obj.find_element_by_css_selector(selector)
    elif find_by == 'partial link':
        return obj.find_elements_by_partial_link_text(selector)

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
           driver = phantomjs.start()
           logging.info('\ngetting the page')
           driver.get('http://s.weibo.com/weibo/{}&Refer=STopic_box'.format(quoted_search_term))
           get_success = True
       except Exception as e:
           logging.info('\nAn error occured trying to visit the page {}'.format(e))
           get_success = False
           get_failure += 1
           driver.quit()
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

   while expand_success is False and expand_failure < 3:
       try:
           expand = find_element(driver, 'partial link', select.EXPAND_TEXT)
           clicked = 0
           logging.info('\nexpanding elements')
           for ele in expand:
               ele.click()
               ## allow time for the click to complete
               time.sleep(5)
               clicked += 1

       except Exception as e:
           logging.info('\nAn error occured trying to expand element {}'.format(e))
           expand_success = False
           expand_failure += 1
           time.sleep(5)

       else:
           collapse = find_element(driver, 'partial link', select.COLLAPSE_TEXT)

            ## if not aligning, restart the driver and revisit the page again
           if clicked != len(collapse):
               logging.info('\nno. of expand and collapse do not match. Start again...')
               get_success = False
               get_failure += 1
               driver.quit()
               time.sleep(10)
               break
           else:
               expand_success = True

   return get_success, get_failure

def scrape(driver):
   full_content_div = find_element(driver, 'css', select.FULL_CONTENT)

   content = []
   url = []
   mid = []

   for ele in full_content_div:
       ## filter posts that contain media, retweet, and links
       if (not find_element(ele, 'css', select.MEDIA)) and \
       (not find_element(ele, 'css', select.REBLOG)) and \
       (not find_element(ele, 'css', select.REBLOG_2)) and \
       (not find_element(ele, 'partial link', select.LINK)) and \
       (not find_element(ele, 'css', select.VIDEO)):

            ## filter short posts that are blank or contain certain keywords
           if (find_element(ele, 'css', select.CONTENT)) and \
           (find_element(ele, 'css singular', select.CONTENT).text != '') and \
           (not(any(word in find_element(ele, 'css singular', select.CONTENT).text for word in filter_words.words))):
               content.append(find_element(ele, 'css singular', select.CONTENT).text)
               mid.append(ele.get_attribute("mid"))

            ## filter long posts that are blank or contain certain keywords
           if (find_element(ele, 'css', select.EXPANDED_CONTENT)) and \
           (find_element(ele, 'css singular', select.EXPANDED_CONTENT).text != '') and \
           (not(any(word in find_element(ele, 'css singular', select.EXPANDED_CONTENT).text for word in filter_words.words))):
               content.append(find_element(ele, 'css singular', select.EXPANDED_CONTENT).text)
               mid.append(ele.get_attribute("mid"))
            
            ## extract url
           if find_element(ele, 'css', select.URL):
               url.append(find_element(ele, 'css singular', select.URL))

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
   EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)

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

   while not queue.empty():
       cur.execute('SELECT url from {}'.format(table))
        ## turn tuple of tuples into list of strings
       exisiting_urls = [''.join(ele) for urls in list(cur.fetchall()) for ele in urls]      
       data = queue.get()

       for i in range(len(data["content"])):
           if data["url"][i] not in exisiting_urls:
               try:
                   cur.execute('''INSERT INTO {} (content, url, uid, pid, mid, pubdate, tested, testdate, status)
                                   VALUES (%s, %s, %s, %s, %s, CURDATE(), DEFAULT, DEFAULT, DEFAULT)'''.format(table), \
                                   (data["content"][i], data["url"][i], data["uid"][i], data["pid"][i], data["mid"][i]))
                   logging.info('saved pid: {}'.format(data["pid"][i]))

                   saved += 1
                   cur.connection.commit()
               except Exception as e:
                   logging.info('\nunable to insert pid {} ... into table. {}'.format(data["pid"][i], e))
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

    for thread in threads:
        thread.start()

    # wait for all threads to complete.
    for thread in threads:
        thread.join()

    try:
        threading.Thread(target=save_to_db, args=(table, queue)).start()
    except Exception as e:
        logging.info('\nunable to start database thread.')
