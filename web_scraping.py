 # encoding: utf-8
from selenium import webdriver
import time
import re
import sys
import local_path
import pymysql
import urllib


FULL_CONTENT_SELECTOR = 'div[class="content clearfix"]'
EXPAND_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"] > a[class="WB_text_opt"]'
COLLAPSE_TEXT_SELECTOR = '收起全文'
CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"]'
EXPANDED_CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[node-type="feed_list_content_full"]'
URL_AND_DATE_SELECTOR = 'div[class="feed_from W_textb"] > a[node-type="feed_list_item_date"]'
MEDIA_SELECTOR = 'div[class="WB_media_wrap clearfix"]'
REBLOG_SELECTOR = 'div[class="comment"]'
LINK_SELECTOR = 'a[class="W_btn_c6"]'


def start_driver(search_term):

    driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
    driver.set_window_size(1124, 850)

    try:
        search_term = search_term.encode('utf-8')
    except UnicodeError:
        print('cannot encode search term to utf-8.')
    quoted_search_term = urllib.parse.quote(search_term)

    try:
        driver.get('http://s.weibo.com/weibo/{}&Refer=STopic_box'.format(quoted_search_term))
    except Exception as e:
        print('An error occured trying to visit the page.')
        print(str(e))

    return driver

def expand_content(diver):

    PAUSE_TIME = 5

    try:
        expand = driver.find_elements_by_css_selector(EXPAND_SELECTOR)
        click_counter = 0
        for ele in expand:
            ele.click()
            ## allow time for the click to complete
            time.sleep(PAUSE_TIME)
            click_counter += 1
        print('click counter: ' + str(click_counter))

    except Exception as e:
        sys.exit('An error occured trying to locate or click the expand element.')
        print(str(e))

    try:
        collapse = driver.find_elements_by_partial_link_text(COLLAPSE_TEXT_SELECTOR)
        print('collapse counter:' + str(len(collapse)))

    except Exception as e:
        print('An error occured trying to locate the collapse element.')
        print(str(e))

    finally:
        if click_counter != len(collapse):
            sys.exit('no. of expand and collapse do not match')

    return


def scrape():

    full_content_div = driver.find_elements_by_css_selector(FULL_CONTENT_SELECTOR)

    content = []
    url_and_date = []

    for ele in full_content_div:
        if not ele.find_elements_by_css_selector(MEDIA_SELECTOR) and  \
        not ele.find_elements_by_css_selector(REBLOG_SELECTOR) and \
        not ele.find_elements_by_css_selector(LINK_SELECTOR):

            if ele.find_element_by_css_selector(CONTENT_SELECTOR).text == '':
                content.append(ele.find_element_by_css_selector(EXPANDED_CONTENT_SELECTOR).text)
            else:
                content.append(ele.find_element_by_css_selector(CONTENT_SELECTOR).text)

            url_and_date.append(ele.find_element_by_css_selector(URL_AND_DATE_SELECTOR))

    url = [ele.get_attribute("href") for ele in url_and_date]
    date = [ele.get_attribute("title") for ele in url_and_date]


    if len(url) != len(date) or len(url) != len(content):
        sys.exit('scrapped content not aligning')

    print('no. of posts collected: ' + str(len(content)))
    print('extract info for saving to database...')
    simplified_url = [u[0:u.find('?')] for u in url]
    uid = [u.split('/')[-2] for u in simplified_url]
    pid = [u.split('/')[-1] for u in simplified_url]
    published_date = [d[0:d.find(' ')] for d in date]

    driver.quit()

    return content, simplified_url, uid, pid, published_date


def save_to_db(content, url, uid, pid, published_date):
    conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE scraping")

    for i in range(len(content)):
        cur.execute('''INSERT INTO cultural_revolution (content, url, uid, pid, pubdate)
                        VALUES (%s, %s, %s, %s, %s)''', \
                        (content[i], url[i], uid[i], pid[i], published_date[i]))

    cur.connection.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    driver = start_driver(sys.argv[1])
    expand_content(driver)
    content, url, uid, pid, published_date = scrape()
    save_to_db(content, url, uid, pid, published_date)
