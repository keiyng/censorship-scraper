# encoding: utf-8
import time
import sys
import re
import os
import threading
import urllib
from queue import Queue
from connections import mysql_database
from variables import element_selector, local_path
from selenium import webdriver

EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)

def get_page(thread_name, search_term, queue):

   get_success = False
   get_failure = 0

   try:
       search_term = search_term.encode('utf-8')
   except UnicodeError:
       sys.exit('cannot encode search term to utf-8.')
   quoted_search_term = urllib.parse.quote(search_term)

   while get_success is False and get_failure < 3:

       try:
           print('starting the driver for {}...'.format(thread_name))
           driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
           ## necessary for elements to be located
           driver.set_window_size(1124, 850)
           print('getting the page for {}...'.format(thread_name))
           driver.get('http://s.weibo.com/weibo/{}&Refer=STopic_box'.format(quoted_search_term))
           get_success = True
       except Exception as e:
           print(str(e))
           print('An error occured trying to visit the page for {}.'.format(thread_name))
           get_success = False
           get_failure += 1
           time.sleep(5)
       else:
           get_success, get_failure = expand_content(thread_name, driver, get_success, get_failure)

   if get_success is True:
       data = scrape(thread_name, driver)
       queue.put(data)
       print('scraping done for {}.'.format(thread_name))

   return


def expand_content(thread_name, driver, get_success, get_failure):

   expand_success = False
   expand_failure = 0

   while expand_success is False and expand_failure < 2:
       try:
           expand = driver.find_elements_by_css_selector(element_selector.EXPAND_SELECTOR)
           clicked = 0
           print('expanding the elements for {}...'.format(thread_name))
           for ele in expand:
               ele.click()
               ## allow time for the click to complete
               time.sleep(5)
               clicked += 1

       except Exception as e:
           print('An error occured trying to click the expand element for {}.'.format(thread_name))
           print(str(e))
           expand_success = False
           expand_failure += 1
           time.sleep(5)

       else:
           collapse = driver.find_elements_by_partial_link_text(element_selector.COLLAPSE_TEXT_SELECTOR)

           if clicked != len(collapse):
               driver.quit()
               get_success = False
               get_failure += 1
               print('no. of expand and collapse do not match for {}. start again...'.format(thread_name))
               time.sleep(10)
               break
           else:
               expand_success = True

   return get_success, get_failure


def scrape(thread_name, driver):

   full_content_div = driver.find_elements_by_css_selector(element_selector.FULL_CONTENT_SELECTOR)

   content = []
   url_and_date = []
   mid = []

   for ele in full_content_div:
       if not ele.find_elements_by_css_selector(element_selector.MEDIA_SELECTOR) and \
       not ele.find_elements_by_css_selector(element_selector.REBLOG_SELECTOR) and \
       not ele.find_elements_by_css_selector(element_selector.LINK_SELECTOR) and \
       not ele.find_elements_by_partial_link_text(element_selector.LINK_SELECTOR_2):

           if ele.find_element_by_css_selector(element_selector.CONTENT_SELECTOR).text == '':
               content.append(ele.find_element_by_css_selector(element_selector.EXPANDED_CONTENT_SELECTOR).text)
           else:
               content.append(ele.find_element_by_css_selector(element_selector.CONTENT_SELECTOR).text)

           url_and_date.append(ele.find_element_by_css_selector(element_selector.URL_AND_DATE_SELECTOR))
           mid.append(ele.get_attribute("mid"))

   content = [EMOJI.sub(r'', text) for text in content]

   url = [ele.get_attribute("href") for ele in url_and_date]
   date = [ele.get_attribute("title") for ele in url_and_date]

   if len(url) != len(date) or len(url) != len(content):
       driver.quit()
       sys.exit('scrapped content not aligning for {}'.format(thread_name))

   print('no. of posts scrapped for {}: {}'.format(thread_name, str(len(content))))
   simplified_url = [u[0:u.find('?')] for u in url]
   uid = [u.split('/')[-2] for u in simplified_url]
   pid = [u.split('/')[-1] for u in simplified_url]
   published_date = [d[0:d.find(' ')] for d in date]

   driver.quit()

   data = {'content': content, 'url': simplified_url, 'uid': uid, 'pid': pid, 'mid': mid, 'published_date': published_date}

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
                                   VALUES (%s, %s, %s, %s, %s, %s, DEFAULT, DEFAULT, DEFAULT)'''.format(table), \
                                   (data["content"][i], data["url"][i], data["uid"][i], data["pid"][i], data["mid"][i], data["published_date"][i]))
                   print('saved pid: {}'.format(data["pid"][i]))

                   saved += 1
                   cur.connection.commit()
               except Exception as e:
                   print(str(e))
                   print('unable to insert pid {} ... into table.'.format(data["pid"][i]))
                   continue
           else:
               skipped += 1

   print('saved: {}; skipped: {}'.format(saved, skipped))

   cur.execute('SELECT COUNT(*) FROM {}'.format(table))
   no_of_rows = str(cur.fetchone()[0])
   print('no. of rows in database: {}'.format(no_of_rows))

   mysql_database.disconnect(conn, cur)

   return



if __name__ == '__main__':
    table = sys.argv[-1]
    queue = Queue()
    threads = []

    try:
        for i in range(1, len(sys.argv) - 1):
            thread = threading.Thread(target=get_page, args=('thread {}'.format(str(i)), sys.argv[i], queue))
            threads.append(thread)
    except Exception as e:
        print(str(e))
        print('unable to start scraping threads.')

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    try:
        threading.Thread(target=save_to_db, args=(table, queue)).start()
    except Exception as e:
        print(str(e))
        print('unable to start database thread.')
