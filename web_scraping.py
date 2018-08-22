from selenium import webdriver
import time
import sys
import local_path
import pymysql


FULL_CONTENT_SELECTOR = 'div[class="content clearfix"]'
EXPAND_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"] > a[class="WB_text_opt"]'
COLLAPSE_TEXT_SELECTOR = '收起全文'
CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[class="comment_txt"]'
EXPANDED_CONTENT_SELECTOR = 'div[class="feed_content wbcon"] > p[node-type="feed_list_content_full"]'
URL_AND_DATE_SELECTOR = 'div[class="feed_from W_textb"] > a[node-type="feed_list_item_date"]'

def start_driver(weibo_url):

    driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
    driver.set_window_size(1124, 850)

    try:
        driver.get(weibo_url)
    except Exception as e:
        print('An error occured trying to visit the page.')
        print(str(e))

    return driver

def expand_elements(diver):

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
    for ele in full_content_div:
        if ele.find_element_by_css_selector(CONTENT_SELECTOR).text == '':
            content.append(ele.find_element_by_css_selector(EXPANDED_CONTENT_SELECTOR).text)
        else:
            content.append(ele.find_element_by_css_selector(CONTENT_SELECTOR).text)

    url_and_date = [ele.find_element_by_css_selector(URL_AND_DATE_SELECTOR) for ele in full_content_div]
    url = [ele.get_attribute("href") for ele in url_and_date]
    date = [ele.get_attribute("title") for ele in url_and_date]


    if len(url) != len(date) or len(url) != len(content):
        sys.exit('scrapped content not aligning')
    else:
        print('scrapped content align.')
        print('proceed to datbase')

    driver.quit()

    return content, url, date

def save_to_db():
    conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
    cur = conn.cursor()
    cur.execute("USE scraping")
    cur.execute('INSERT INTO cultural_revolution (content, pubdate, url, mid, uid, pid) VALUES ("test_content", "1991-02-18", "test_url", "test_mid", "test_uid", "test_pid")')
    cur.connection.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    driver = start_driver(sys.argv[1])
    expand_elements(driver)
    content, url, date = scrape()
    save_to_db()
