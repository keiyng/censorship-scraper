# encoding: utf-8
import sys
import time
# import signal
import local_path
import connect_to_db
from selenium import webdriver

def timeout_handler(signum, frame):
    raise Exception("the process took too long to complete")
    sys.exit()

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
##commit -am "call expand_elements() inside get_page(); add while loops to rerun functions/statements in case of exceptions; adjust other exception handling"

def check():

    if len(data) > 0:

        conn, cur = connect_to_db.connect()

        print('starting the driver...')
        driver = webdriver.PhantomJS(executable_path=local_path.phantomjs_path)
        driver.set_window_size(1124, 850)

        for url, pid in data:
            try:
                driver.get(url)
                ## allow time for page to load (or possibly redirect)
                print('visiting {}'.format(url))
                time.sleep(20)
            except Exception as e:
                print(str(e))
                print('An error occured trying to visit {}.'.format(url))
                continue
            else:
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
        print('unable to update record. pid: {}'.format(pid))

    finally:
        cur.connection.commit()


if __name__ == '__main__':
    data = select_posts(sys.argv[1])
    check()
