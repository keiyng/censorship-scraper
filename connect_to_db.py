import sys
import pymysql

def connect():
    try:
        conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock', user='root', passwd=None, db='mysql', charset='utf8')
        cur = conn.cursor()
        cur.execute("USE scraping")
    except Exception as e:
        print(str(e))
        sys.exit('unable to connect to database')
    else:
        return conn, cur
