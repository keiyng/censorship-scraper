# encoding: utf-8
import sys
import time
import local_path
import connect_to_db
from selenium import webdriver

def select_posts(table):
    conn, cur = connect_to_db.connect()
    cur.execute(
    '''SELECT url, pid from {}
    WHERE pubdate < CURDATE() - INTERVAL 1 DAY
    AND tested = "not yet" '''.format(table))

    data = list(cur.fetchall())
    print('no. of posts to be tested: {}'.format(len(data)))

    cur.close()
    conn.close()

    return data


def check(data):

    if len(data) > 0:

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

            update_db(url, pid, current_url, conn, cur, sys.argv[1])

        cur.close()
        conn.close()
        driver.quit()

    return

def update_db(url, pid, current_url, conn, cur, table):

    try:
        if pid not in current_url:
            print('***pid {} not found in current url: {}'.format(pid, current_url))
            print('original url is: {} ***'.format(url))

            cur.execute('''UPDATE {}
            SET tested = "yes", testdate = CURDATE(), status = "not available"
            WHERE pid = {}'''.format(table), \
            (pid))

        else:
            cur.execute('''UPDATE {}
            SET tested = "yes", testdate = CURDATE(), status = "available"
            WHERE pid = %s'''.format(table), \
            (pid))

    except Exception as e:
        cur.close()
        conn.close()
        print(str(e))
        print('unable to update record.')

    finally:
        cur.connection.commit()


if __name__ == '__main__':
    data = select_posts(sys.argv[1])
    check(data)
