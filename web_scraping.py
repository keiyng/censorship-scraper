 # encoding: utf-8
import time
import sys
import signal
import local_path
import connect_to_db
import urllib
from selenium import webdriver


FULL_CONTENT_SELECTOR = 'div[class="content clearfix"]'
EXPAND_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"] > a[class="WB_text_opt"]'
COLLAPSE_TEXT_SELECTOR = '收起全文'
CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"]'
EXPANDED_CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[node-type="feed_list_content_full"]'
URL_AND_DATE_SELECTOR = 'div[class="feed_from W_textb"] > a[node-type="feed_list_item_date"]'
MEDIA_SELECTOR = 'div[class="WB_media_wrap clearfix"]'
REBLOG_SELECTOR = 'div[class="comment"]'
LINK_SELECTOR = 'a[class="W_btn_c6"]'

def timeout_handler(signum, frame):
    raise Exception("the process took too long to complete")
    sys.exit()


def get_page(search_term):

    get_success = False

    ## allow 2 minutes max to complete getting page and expanding elements
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)

    try:
        search_term = search_term.encode('utf-8')
    except UnicodeError:
        sys.exit('cannot encode search term to utf-8.')
    quoted_search_term = urllib.parse.quote(search_term)

    while get_success is False:

        try:
            print('starting the driver...')
            driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
            ## necessary for elements to be located
            driver.set_window_size(1124, 850)
            print('getting the page...')
            driver.get('http://s.weibo.com/weibo/{}&Refer=STopic_box'.format(quoted_search_term))
            get_success = True
        except Exception as e:
            print(str(e))
            print('An error occured trying to visit the page.')
            get_success = False
            time.sleep(5)
        else:
            get_success = expand_content(driver, get_success)

    signal.alarm(0)

    return driver

def expand_content(driver, get_success):

    expand_success = False

    while expand_success is False:

        try:
            expand = driver.find_elements_by_css_selector(EXPAND_SELECTOR)
            clicked = 0
            print('expanding the elements...')
            for ele in expand:
                ele.click()
                ## allow time for the click to complete
                time.sleep(5)
                clicked += 1

        except Exception as e:
            print('An error occured trying to click the expand element.')
            print(str(e))
            expand_success = False
            time.sleep(5)

        else:
            collapse = driver.find_elements_by_partial_link_text(COLLAPSE_TEXT_SELECTOR)

            if clicked != len(collapse):
                driver.quit()
                get_success = False
                print('no. of expand and collapse do not match. start again...')
                time.sleep(10)
                break
            else:
                expand_success = True


    return get_success


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
        driver.quit()
        sys.exit('scrapped content not aligning')

    print('no. of posts scrapped: {}'.format(str(len(content))))
    print('extract info for saving to database...')
    simplified_url = [u[0:u.find('?')] for u in url]
    uid = [u.split('/')[-2] for u in simplified_url]
    pid = [u.split('/')[-1] for u in simplified_url]
    published_date = [d[0:d.find(' ')] for d in date]

    driver.quit()

    return content, simplified_url, uid, pid, published_date


def save_to_db(table):
    saved = 0
    skipped = 0

    conn, cur = connect_to_db.connect()

    cur.execute('SELECT url from {}'.format(table))
    ## turn tuple of tuples into list of strings
    exisiting_urls = [''.join(ele) for urls in list(cur.fetchall()) for ele in urls]


    for i in range(len(content)):
        if url[i] not in exisiting_urls:
            try:
                print('inserting data {}...'.format(content[i])[:10])
                cur.execute('''INSERT INTO {} (content, url, uid, pid, pubdate, tested, testdate, status)
                                VALUES (%s, %s, %s, %s, %s, DEFAULT, DEFAULT, DEFAULT)'''.format(table), \
                                (content[i], url[i], uid[i], pid[i], published_date[i]))
                print('saved content: {} ...'.format(content[i][:15]))
                saved += 1
            except Exception as e:
                print(str(e))
                print('unable to insert data into databse.')
                continue
        else:
            skipped += 1


    print('finished saving to database')
    print('saved: {}; skipped: {}'.format(saved, skipped))

    cur.execute('SELECT COUNT(*) FROM {}'.format(table))
    no_of_rows = str(cur.fetchone()[0])
    print('no. of rows in database: {}'.format(no_of_rows))

    cur.connection.commit()

    cur.close()
    conn.close()

    return

if __name__ == '__main__':
    driver = get_page(sys.argv[1])
    content, url, uid, pid, published_date = scrape()
    save_to_db(sys.argv[2])
