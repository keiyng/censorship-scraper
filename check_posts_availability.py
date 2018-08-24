# encoding: utf-8
import sys
import time
# import pymysql
import local_path
import connect_to_db
from selenium import webdriver

def select_posts():
    conn, cur = connect_to_db.connect()
    cur.execute(
    '''SELECT url, pid from cultural_revolution
    WHERE pubdate < CURDATE() - INTERVAL 1 DAY
    ## AND tested = "not yet" ''')


    data = list(cur.fetchall())
    print('no. of posts to be tested: {}'.format(len(data)))

    cur.close()
    conn.close()

    return data


def check(data):

    driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
    driver.set_window_size(1124, 850)

    conn, cur = connect_to_db.connect()

    for url, pid in data:
        try:
            driver.get(url)
            ## allow time for page to load (or possibly redirect)
            time.sleep(20)
        except Exception as e:
            print(str(e))
            print('An error occured trying to visit {}.'.format(url))

        print('visiting {}'.format(url))
        current_url = driver.current_url

        update_db(url, pid, current_url, conn, cur)

    cur.close()
    conn.close()
    driver.quit()

def update_db(url, pid, current_url, conn, cur):

    try:
        if pid not in current_url:
            print('***pid {} not found in current url: {}'.format(pid, current_url))
            print('original url is: {} ***'.format(url))

            cur.execute('''UPDATE cultural_revolution
            SET tested = "yes", testdate = CURDATE(), status = "not available"
            WHERE pid = %s''', \
            (pid))

        else:
            cur.execute('''UPDATE cultural_revolution
            SET tested = "yes", testdate = CURDATE(), status = "available"
            WHERE pid = %s''', \
            (pid))

    except Exception as e:
        print(str(e))
        print('unable to update record.')

    finally:
        cur.connection.commit()


if __name__ == '__main__':
    data = select_posts()
    check(data)
