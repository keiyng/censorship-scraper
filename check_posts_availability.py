# encoding: utf-8
import sys
import time
import pymysql
import local_path
from selenium import webdriver

def select_posts():
    try:
        conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
    except Exception as e:
        print(str(e))
        sys.exit('unable to connect to database')

    cur = conn.cursor()
    cur.execute("USE scraping")
    cur.execute('SELECT url, pid from cultural_revolution WHERE pubdate > CURDATE() - INTERVAL 1 DAY')

    urls_to_check = []
    pid_to_check = []
    for post in list(cur.fetchall()):
        urls_to_check.append(post[0])
        pid_to_check.append(post[1])

    cur.close()
    conn.close()

    return urls_to_check, pid_to_check


def check(urls_to_check, pid_to_check):

    driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
    driver.set_window_size(1124, 850)

    for url in urls_to_check:
        try:
            driver.get(url)
            ## allow time for page to load (or possibly redirect)
            time.sleep(20)
            print('visiting {}'.format(driver.current_url))

        except Exception as e:
            print(str(e))
            print('An error occured trying to visit {}.'.format(url))


    driver.quit()

    for url in urls_to_check:
        print(url)



if __name__ == '__main__':
    urls_to_check, pid_to_check = select_posts()
    check(urls_to_check, pid_to_check)
