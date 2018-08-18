from selenium import webdriver
import time
import sys
import local_path


full_content_selector = 'div[class="content clearfix"]'
expand_selector = 'div[class="feed_content wbcon"] > p[class="comment_txt"] > a[class="WB_text_opt"]'
collapse_text_selector = '收起全文'
content_selector = 'div[class="feed_content wbcon"] > p[class="comment_txt"]'
expanded_content_selector = 'div[class="feed_content wbcon"] > p[node-type="feed_list_content_full"]'
url_and_date_selector = 'div[class="feed_from W_textb"] > a[node-type="feed_list_item_date"]'

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

    PAUSE_TIME = 2

    try:
        expand = driver.find_elements_by_css_selector(expand_selector)
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
        collapse = driver.find_elements_by_partial_link_text(collapse_text_selector)
        print('collapse counter:' + str(len(collapse)))

    except Exception as e:
        print('An error occured trying to locate the collapse element.')
        print(str(e))

    finally:
        if click_counter != len(collapse):
            sys.exit('no. of expand and collapse do not match')

    return


def scrape():

    full_content_div = driver.find_elements_by_css_selector(full_content_selector)

    content = []
    for ele in full_content_div:
        if ele.find_element_by_css_selector(content_selector).text == '':
            content.append(ele.find_element_by_css_selector(expanded_content_selector))
        else:
            content.append(ele.find_element_by_css_selector(content_selector))

    url_and_date = [ele.find_element_by_css_selector(url_and_date_selector) for ele in full_content_div]
    url = [ele.get_attribute("href") for ele in url_and_date]
    date = [ele.get_attribute("title") for ele in url_and_date]

    if len(url) != len(date) or len(url) != len(content):
        sys.exit('scrapped content not aligning')

    driver.quit()

    return content, url, date



if __name__ == '__main__':
    driver = start_driver(sys.argv[1])
    expand_elements(driver)
    content, url, date = scrape()
