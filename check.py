import sys
import time
import logging
import weibo_api
import requests as r
from connections import mysql_database, phantomjs

def selectData(cur, interval, table, test):
    cur.execute('''SELECT url, pid, mid from {}
        WHERE pubdate < CURDATE() - INTERVAL {} DAY
        AND {} = "not yet" '''.format(table, interval, test))

def updateData(cur, table, test, date, status, availability, mid, error=None):
    cur.execute('''UPDATE {}
    SET {} = "yes", {} = CURDATE(), {} = %s, error = %s
    WHERE mid = %s'''.format(table, test, date, status), \
    (availability, error, mid))

def select(num, table):
    conn, cur = mysql_database.connect()
    ## 1st test after 2 days
    if num == '1':
        selectData(cur, '2', table, 'tested')
    ## 2nd test after 14 days
    elif num == '2':
        selectData(cur, '14', table, 'retested')
    else:
        sys.exit('unable to select appropriate data to test')

    data = list(cur.fetchall())
    logging.info('\nno. of posts to be tested: {}'.format(len(data)))

    mysql_database.disconnect(conn, cur)

    return data

def get_page():
    if len(data) > 0:
        conn, cur = mysql_database.connect()
        driver = phantomjs.start()
        counter = 0

        for url, pid, mid in data:
            try:
                driver.get(url)
                counter += 1
                print('{} visiting {}'.format(counter, url))
                ## allow time for page to load (or possibly redirect)
                time.sleep(20)
            except Exception as e:
                logging.info('An error occured trying to visit {}. \n{}'.format(url, e))
                continue
            else:
                current_url = driver.current_url
                update_db(driver, url, pid, mid, current_url, conn, cur, num, table)

        mysql_database.disconnect(conn, cur)
        driver.quit()

    return

def update_db(driver, url, pid, mid, current_url, conn, cur, num, table):
    try:
        ## if not available
        if pid not in current_url:
            logging.info('\npid {} not found in current url: {}'.format(pid, current_url))
            logging.info('\noriginal url is: {}'.format(url))
            if num == '1':
                updateData(cur, table, 'tested', 'testdate', 'status', 'not available', mid)             
            elif num == '2':
                request = r.get('{}id={}&access_token={}'.format(weibo_api.BASE_STATUS_REQUEST_URL, mid, weibo_api.ACCESS_TOKEN_1)) 
                response = request.json()
                error = response['error']
                print(error)

                if 'limit' in error:
                    sys.exit()
                if 'Permission' in error:
                    driver.get(url[:-9])
                    print('visiting user page {}'.format(url[:-9]))
                    time.sleep(20)
                    user_url = driver.current_url
                    print(user_url)
                    if user_url.endswith('.com/us'):
                        updateData(cur, table, 'retested', 'retestdate', 'status_2', 'protected', mid)
                    else:
                        updateData(cur, table, 'retested', 'retestdate', 'status_2', 'not available', mid, error)
                else:
                    updateData(cur, table, 'retested', 'retestdate', 'status_2', 'not available', mid, error)
        ## if available
        else:
            if num == '1':
                updateData(cur, table, 'tested', 'testdate', 'status', 'available', mid)
            elif num == '2':
                updateData(cur, table, 'retested', 'retestdate', 'status_2', 'available', mid)

    except Exception as e:
        print('unable to update {}. {}'.format(pid, e))

    else:
        cur.connection.commit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(message)s')

    num = sys.argv[1]
    table = sys.argv[2]

    if num != '1' and num != '2':
        sys.exit('invalid argument for check number')
    
    data = select(num, table)
    get_page()
