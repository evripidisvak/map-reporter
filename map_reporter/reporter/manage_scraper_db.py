import sqlite3
from sqlite3 import Error
from datetime import datetime
from decimal import Decimal


# import psycopg2

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file, timeout=10)
    except Error as e:
        print(e)
    return conn


def get_all_urls(conn):
    """
    Query and return all page urls
    """
    c = conn.cursor()
    c.execute('''
    SELECT url FROM pages
    ''')
    rows = c.fetchall()
    return rows


def get_page_list(conn):
    """
    Query and return all page ids
    """
    c = conn.cursor()
    c.execute('''
    SELECT * FROM reporter_page WHERE product_id IN (SELECT id FROM reporter_product WHERE active=1)
    ''')
    rows = c.fetchall()
    return rows


def get_or_insert_shop(shop_name, conn):
    """
    Find and return the shop_id by shop_name. If this shop_name does not exist in the database, insert it
    """
    c = conn.cursor()
    try:
        shop_id = c.execute('''
        SELECT id FROM reporter_shop WHERE name LIKE ?
        ''', (shop_name,)).fetchone()
        if shop_id is None:
            shop_id = insert_new_shop(shop_name, conn)
        else:
            shop_id = shop_id[0]
        return shop_id
    except Exception as e:
        print(e)
        return False


def insert_new_shop(shop_name, conn):
    """
    Insert new shop in shops table of database
    """
    c = conn.cursor()
    try:
        c.execute('''
        INSERT INTO reporter_shop(name, key_account) VALUES (?,?)
        ''', (shop_name, 0))
        conn.commit()
        shop_id = c.execute('''
        SELECT id FROM reporter_shop WHERE name LIKE ?
        ''', (shop_name,)).fetchone()
        return shop_id[0]
    except Exception as e:
        print(e)
        return False


def insert_product_prices(price_list, product_id, shop, official_reseller, db):
    """
    Insert scraped prices in the db
    """
    conn = create_connection(db)
    c = conn.cursor()
    timestamp = datetime.now()
    try:
        for index in range(len(price_list)):
            shop_id = get_or_insert_shop(shop[index], conn)
            price = float(price_list[index])
            indx_off_res = official_reseller[index]
            c.execute('''
            INSERT INTO reporter_retailprice(price,timestamp,official_reseller,product_id,shop_id) VALUES(?, ?, ?, ?, ?)
            ''', (price, timestamp, indx_off_res, product_id, shop_id))
        conn.commit()
        print('Prices of product with id', product_id, 'inserted successfully')
        return True
    except Error as e:
        print(e)
        return False
