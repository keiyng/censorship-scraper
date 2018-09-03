# encoding: utf-8
import sys
import time
from connections import mysql_database
from variables import local_path
from selenium import webdriver

def select_posts(table):
    conn, cur = mysql_database.connect()
    cur.execute(
    '''SELECT url, pid from {}
    WHERE pubdate < CURDATE() - INTERVAL 2 DAY
    AND tested = "not yet" '''.format(table))

    data = list(cur.fetchall())
    print('no. of posts to be tested: {}'.format(len(data)))

    mysql_database.disconnect(conn, cur)

    return data

def check():

    if len(data) > 0:

        conn, cur = mysql_database.connect()

        print('starting the driver...')
        driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
        driver.set_window_size(1124, 850)

        counter = 0

        for url, pid in data:
            try:
                driver.get(url)
                ## allow time for page to load (or possibly redirect)
                counter += 1
                print('{} visiting {}'.format(counter, url))
                time.sleep(20)
            except Exception as e:
                print(str(e))
                print('An error occured trying to visit {}.'.format(url))
                continue
            else:
                current_url = driver.current_url
                update_db(url, pid, current_url, conn, cur, sys.argv[1])

        mysql_database.disconnect(conn, cur)
        driver.quit()

    return

def update_db(url, pid, current_url, conn, cur, table):

    try:
        if pid not in current_url:
            print('***pid {} not found in current url: {}'.format(pid, current_url))
            print('original url is: {} ***'.format(url))

            cur.execute('''UPDATE {}
            SET tested = "yes", testdate = CURDATE(), status = "not available"
            WHERE pid = %s'''.format(table), \
            (pid))

        else:
            cur.execute('''UPDATE {}
            SET tested = "yes", testdate = CURDATE(), status = "available"
            WHERE pid = %s'''.format(table), \
            (pid))

    except Exception as e:
        print(str(e))
        print('unable to update record. pid: {}'.format(pid))

    else:
        cur.connection.commit()


if __name__ == '__main__':
    data = select_posts(sys.argv[1])
    check()
