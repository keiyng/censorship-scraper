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

    to_check = {}

    for post in list(cur.fetchall()):
        to_check.update({post[0]: post[1]})

    cur.close()
    conn.close()


    return to_check


def check(to_check):

    driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
    driver.set_window_size(1124, 850)

    for url, pid in to_check.items():
        try:
            driver.get(url)
            ## allow time for page to load (or possibly redirect)
            time.sleep(20)
            current_url = driver.current_url
            print('visiting {}'.format(current_url))

            if pid not in current_url:
                print('pid {} not found in current url: {}'.format(pid, current_url))
                print('original url is: {}'.format(url))


        except Exception as e:
            print(str(e))
            print('An error occured trying to visit {}.'.format(url))

    driver.quit()



if __name__ == '__main__':
    to_check = select_posts()
    check(to_check)
