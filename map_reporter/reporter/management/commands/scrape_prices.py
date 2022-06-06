import concurrent.futures
import logging.handlers
import os
import random
import smtplib
import sys
import time
import traceback
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from itertools import product, zip_longest

import pandas as pd
import psutil
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from Proxy_List_Scrapper import Scrapper
from reporter.models import *
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

startTime = datetime.now()


class Command(BaseCommand):
    help = 'Runs the scraper'

    # if __name__ == '__main__':

    def handle(self, *args, **options):
        global proxy
        global my_proxies
        my_proxies = []
        records = []
        page_list = Page.objects.all()
        failedRecords = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Start the load operations and mark each future with its URL
            while len(page_list) > 0:
                future_to_url = {executor.submit(
                    parse_urls, url): url for url in page_list}
                page_list = []
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    time.sleep(random.random() + 2)
                    try:
                        data = future.result()
                    except Exception as exc:
                        print('%r generated an exception: %s' %
                              (url, traceback.format_exc()))
                        # print('%r generated an exception: %s' % (url, exc))
                        page_list.append(url)
                    else:
                        if data != 'Key Account':
                            records.append(data)
                            todayDate = datetime.today().strftime('%d-%m-%Y')
                            time_needed = datetime.now() - startTime
                            time_needed = str(time_needed)
                            print('*** *** *** Processed URLs: ' +
                                format(len(records)) + ' in ' + format(time_needed))
                        else:
                            print('Key account page scraped: ', url)
        geckodriver_proc = "geckodriver"  # or chromedriver or IEDriverServer
        chromedriver_proc = "chromedriver"  # or geckodriver or IEDriverServer
        # for proc in psutil.process_iter():
            # check whether the process name matches
            # if geckodriver_proc in proc.name() or chromedriver_proc in proc.name():
            #     proc.kill()
        create_files_and_send_emails(records)

        print('Time to complete: ', time_needed)
        print('*************OK*******************')
        # sys.exit()


def parse_urls(page_list_item):
    # TODO Make sure the we get the correct values, no matter the way the list  page_list_item is sorted
    page_id = page_list_item.id
    product_id = page_list_item.product_id
    source_id = page_list_item.source_id
    url = page_list_item.url
    global my_proxies
    global proxy
    info = []
    if my_proxies is None or len(my_proxies) <= 10:
        my_proxies = get_new_proxies()
    driver = ""
    while True:
        try:
            proxy_tmp = random.choice(my_proxies)
            proxy = proxy_tmp
            print('+++ +++ Selecting new proxy: ', proxy)
            print('+++ Proxies left: ', len(my_proxies))
            print('+++ Proxy used: ', proxy)
            print('+++ URL: ', url)
            options = Options()
            options.headless = True

            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(30)
            # this_user_agent = driver.execute_script("return navigator.userAgent;")
            # print(this_user_agent)

            # url = 'https://ipecho.net/'

            # get web page
            driver.get(url)
            break
        except:
            print("~~ Connection error, removing proxy from list")
            # no_connect = True
            driver.quit()
            if proxy in my_proxies:
                my_proxies.remove(proxy)
                print("*** Proxy Removed *** ", len(my_proxies))
            if len(my_proxies) <= 50:
                print('&&& Remaining my_proxies: ', len(
                    my_proxies), '. Trying to find new my_proxies')
                my_proxies = get_new_proxies()

    # sleep for random amount of time
    secs = random.random() + 1
    time.sleep(secs)

    if source_id == 1: #Skroutz
    # execute script to scroll down the page
        try:
            len_of_page = driver.execute_script(
                "var len_of_page=document.body.scrollHeight;return len_of_page;")
        except:
            # driver.quit()
            raise ValueError('Page has no length')
        current_height = 0
        while current_height < len_of_page:
            scroll_height = random.randint(250, 350)
            driver.execute_script(
                "window.scrollBy({top: " + str(scroll_height) + ", left: 0, behavior: 'smooth'});")
            time.sleep(random.random() + 0.5)
            current_height = current_height + scroll_height

        # sleep for random amount of time
        time.sleep(random.random() + 0.3)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit()
        # if product does not have a dedicated page
        if soup.find("h1", class_="page-title"):
            h1 = soup.find("h1", class_="page-title")
            print(h1)
        else:
            print("NO PROPER H1 FOUND")
        if soup.find("a", class_="closable-tag"):
            title = soup.find("a", class_="closable-tag")
            if title:
                title = title.text
            shop = soup.findAll("button", class_="js-shop-info-link")
            for s in shop:
                if s and len(s) > 0:
                    shop[shop.index(s)] = s.text
                else:
                    shop[shop.index(s)] = 'NAN'
            price = soup.findAll("a", class_="js-sku-link product-link")
            for pri in price:
                if pri and len(pri) > 0:
                    for span in pri.findAll('span'):
                        span.decompose()
                    price[price.index(pri)] = pri.text.strip(
                        ' €').replace('.', '').replace(',', '.')
                else:
                    price[price.index(pri)] = '9999'
            off_seller = soup.findAll("span", class_="payment-options")
            for os in off_seller:
                if 'Επίσημος μεταπωλητής' in os.text:
                    off_seller[off_seller.index(os)] = 'Επίσημος μεταπωλητής'
                else:
                    off_seller[off_seller.index(os)] = ''
        else:
            # if product has a dedicated product page
            title = soup.find("h1", class_="page-title")
            if title:
                title = title.text
            shop = soup.findAll("p", class_="shop-name")
            if soup.find("span", class_="obsolete-sku") or soup.find("div", class_="obsolete-sku") or soup.find("div", class_="unavailable-sku"):
                shop = 'Μ/Δ'
                price = '9999'
                off_seller = 'Μ/Δ'
            else:
                if len(shop) < 1:
                    raise ValueError
                price = soup.findAll("strong", class_="dominant-price")
                off_seller = soup.findAll("div", class_="shop-info-row")
                # Clean data
                if title and len(title) > 0:
                    title = title.strip()
                else:
                    # title = 'NAN'
                    raise TypeError
                for s in shop:
                    if s and len(s) > 0:
                        shop[shop.index(s)] = s.text
                    else:
                        shop[shop.index(s)] = 'NAN'
                for pri in price:
                    if pri and len(pri) > 0:
                        if pri.find('span', 'vatfree-price'):
                            pri.find('span', 'vatfree-price').decompose()
                        price[price.index(pri)] = pri.text.strip(
                            ' €').replace('.', '').replace(',', '.')
                    else:
                        price[price.index(pri)] = '9999'
                for os in off_seller:
                    if 'Επίσημος μεταπωλητής' in os.text:
                        off_seller[off_seller.index(os)] = 1
                    else:
                        off_seller[off_seller.index(os)] = 0
        info.append(url)
        info.append(title)
        info.append(shop)
        info.append(price)
        info.append(off_seller)
        # info.append(page_id)
        # save_prices(price, product_id, shop, off_seller, source_id)

    elif source_id == 2: #Plaisio
        soup = BeautifulSoup(driver.page_source, 'lxml')
        if soup.find('body', class_="neterror") or soup.find('h1').text == 'Access Denied':
            print('*** Network Error ***')
            raise ValueError('Network Error')
        pricear = soup.select(".pdp-price-container .pdp-price-container__price .product-price .price")
        if pricear:
            price = pricear[0].text.strip(' €').strip().replace(',', '.')
            price = [price]
            shop = ['Plaisio']
            off_seller = ['1']
            # save_prices(price, product_id, shop, off_seller, source_id)

    elif source_id == 3: #Praktiker
        soup = BeautifulSoup(driver.page_source, 'lxml')
        if soup.find('body', class_="neterror") or soup.find('h1').text == 'Access Denied':
            print('*** Network Error ***')
            raise ValueError('Network Error')
        pricear = soup.select("span.product__price.product__price--main")
        pricear_sale = soup.select("span.product__price.product__price--main.product__price--discounted")
        shop = 'Praktiker'
        if pricear:
            price = pricear[0].text.strip().replace(',', '.').rstrip().strip('€')
        elif pricear_sale:
            price = pricear_sale[0].text.strip().replace(',', '.').rstrip().strip('€')
        if price is not None:
            price = [price]
            shop = ['Praktiker']
            off_seller = ['1']
            # save_prices(price, product_id, shop, off_seller, source_id)
    
    elif source_id == 4: #Kotsovolos
        pricear = soup.select(".prDetail .priceWithVat .simplePrice")
        pricear_sale = soup.select(".prDetail .priceWithVat .price")
        shop = 'Kotsovolos'
        if pricear:
            pricear[0].find('span', 'main-price').decompose()
            price = pricear[0].text.strip().replace(',', '.')
        elif pricear_sale:
            for elem in pricear_sale:
                if elem.find('span', 'main-price'):
                    elem.find('span', 'main-price').decompose()
                    price = elem.text.strip().replace(',', '.')
        if price is not None:
            price = [price]
            shop = ['Kotsovolos']
            off_seller = ['1']
            # save_prices(price, product_id, shop, off_seller, source_id)

    elif source_id == 5: #Public
        pricear = soup.select(
            "div.product__price.product__price--xlarge.text-primary")
        if pricear and pricear != '' and '\n' not in pricear[0].text:
            price = pricear[0].text.strip(' €').replace(',', '.')
        if price is not None:
            price = [price]
            shop = ['Public']
            off_seller = ['1']
            # save_prices(price, product_id, shop, off_seller, source_id)

    elif source_id == 6: #You
        pricear = soup.select("div.price.new-price span.final-price")
        shop = 'You'
        if pricear:
            price = pricear[0].text.strip(' €').replace(',', '.')
        if price is not None:
            price = [price]
            shop = ['You']
            off_seller = ['1']
    
    elif source_id == 7: #Media Markt
        pricear = soup.select("div.article__price.ng-star-inserted")
        if pricear:
            price = pricear[0].text.replace(',', '.')
        if price is not None:
            price = [price]
            shop = ['Media Markt']
            off_seller = ['1']

    elif source_id == 8: #Germanos
        pricear = soup.select("div.product-price span.price")
        pricear_sale = soup.select("div.product-price span.special-price")
        if pricear:
            price = pricear[0].text.strip().replace(',', '.').rstrip().strip('€')
        elif pricear_sale:
            price = pricear_sale[0].text.strip().replace(',', '.').rstrip().strip('€')
        if price is not None:
            price = [price]
            shop = ['Germanos']
            off_seller = ['1']
    
    elif source_id == 9: #Electronet
        pricear = soup.select(
            "td.commerce-price-savings-formatter-price span.price-amount")
        if pricear:
            price = pricear[0].text.strip().replace(',', '.').rstrip().strip('€').strip()
        if price is not None:
            price = [price]
            shop = ['Electronet']
            off_seller = ['1']

    else:
        print('A scraper for this source does not exist')
        return True

    # info.append(url)
    # info.append(title)
    # info.append(shop)
    # info.append(price)
    # info.append(off_seller)
    # info.append(page_id)
    # save_prices(price, product_id, shop, off_seller)
    try:
        save_prices(price, product_id, shop, off_seller, source_id)
    except Exception as e:
        print(e)
        return False
    if source_id == 1:
        return info
    else:
        return 'Key Account'


def save_prices(price_list, product_id, shop, official_reseller, source_id):
    # The below stores time in UTC, but Django can convert and compare time by itself using the user's timezone. In case you definately need the local time use this: timenow = timezone.localtime(timezone.now())
    timenow = timezone.now()
    product_obj = Product.objects.get(id=product_id)
    source_obj = Source.objects.get(id=source_id)
    for index in range(len(price_list)):
        rp = RetailPrice(
            price=float(price_list[index]),
            timestamp=timenow,
            product=product_obj,
            shop=Shop.objects.get_or_create(name=shop[index], source=source_obj)[0],
            official_reseller=official_reseller[index]
            )
        rp.save()

# ~ Get my_proxies


def get_new_proxies():
    proxies_list = []
    scrapper = Scrapper(category='ALL', print_err_trace=False)
    proxies_obj = scrapper.getProxies()

    for item in proxies_obj.proxies:
        proxies_list.append(item.ip + ":" + item.port)

    return proxies_list

# Send the emails


def send_mail(send_to, subject, text, files, isTls=True):
    msg = MIMEMultipart()
    msg['From'] = 'e.vakalis@soundstar.gr'
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    server = 'mail.soundstar.gr'
    port = 25
    username = 'e.vakalis@soundstar.gr'
    password = 'Ilk4b31@'
    for a_file in files:
        attachment = open('Reports/' + a_file, 'rb')
        file_name = a_file
        # file_name = os.path.basename(a_file)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        part.add_header('Content-Disposition',
                        'attachment', filename=file_name)
        encoders.encode_base64(part)
        msg.attach(part)
    # part = MIMEBase('application', "octet-stream")
    # part.set_payload(open(files, "rb").read())
    # encoders.encode_base64(part)
    # part.add_header('Content-Disposition', 'attachment', filename=files)
    # msg.attach(part)

    # context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
    # SSL connection only working on Python 3+
    # Using smtplib.SMTP_SSL() instead of smtplib.SMTP() works for me. Try this.
    smtp = smtplib.SMTP(server, port)
    try:
        if isTls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(username, send_to, msg.as_string())
        smtp.quit()
    except:
        time.sleep(120)
        try:
            if isTls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.sendmail(username, send_to, msg.as_string())
            smtp.quit()
        except:
            logging.exception('Email sending error:')


def get_col_widths(dataframe):
    # First we find the maximum length of the index column
    idx_max = max([len(str(s)) for s in dataframe.index.values] +
                  [len(str(dataframe.index.name))])
    # Then, we concatenate this to the max of the lengths of column name and its values for each column, left to right
    return [idx_max] + [max([len(str(s)) for s in dataframe[col].values] + [len(col)]) for col in dataframe.columns]


def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'black'
    return 'color: %s' % color

# Create an xls file, adjust column widths and save it


def autofit_and_save(writer, dataframeaf):
    dataframeaf.to_excel(writer, sheet_name='Sheet1', index=False)
    # workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    for i, width in enumerate(get_col_widths(dataframeaf)[1:]):
        worksheet.set_column(i, i, width * 1.05)
    writer.save()

# Create an xls file, adjust column widths, colour negative Diffs red and save it


def autofit_colour_and_save(writer, dataframeaf):
    dataframeaf.to_excel(writer, sheet_name='Sheet1', index=False)
    dataframeaf.style.applymap(color_negative_red, subset=['Diff', 'Diff%']).to_excel(
        writer, sheet_name='Sheet1', index=False)
    # workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    for i, width in enumerate(get_col_widths(dataframeaf)[1:]):
        worksheet.set_column(i, i, width * 1.05)
    writer.save()


def xplode(df, explode, zipped=True):
    method = zip_longest if zipped else product

    rest = {*df} - {*explode}

    zipped = zip(zip(*map(df.get, rest)), zip(*map(df.get, explode)))
    tups = [tup + exploded
            for tup, pre in zipped
            for exploded in method(*pre)]

    return pd.DataFrame(tups, columns=[*rest, *explode])[[*df]]


def create_files_and_send_emails(records):
    recordsDf = pd.DataFrame.from_records(records)
    recordsDf.columns = ['URL', 'SKR_Title','SKR_Shop', 'SKR_Price', 'Official_Seller']

    writer = pd.ExcelWriter("Reports\\recordsDf.xlsx", engine='xlsxwriter')
    autofit_and_save(writer, recordsDf)

    webSkrList = pd.read_csv("Reports\\map-products.csv")
    webSkrList['MAP'] = webSkrList['MAP'].astype(float)

    mergedData = xplode(recordsDf, ['SKR_Shop', 'SKR_Price', 'Official_Seller'])
    mergedData = pd.merge(mergedData, webSkrList, on='URL', how='inner')

    # Update sellers file
    sellers = pd.read_excel('Reports\\stores-sellers.xlsx')
    sellers_upd = pd.DataFrame(mergedData['SKR_Shop'].drop_duplicates())
    sellers_upd.rename(columns={'SKR_Shop': 'Κατάστημα'}, inplace=True)
    sellers_upd = pd.merge(sellers_upd, sellers,on='Κατάστημα', how='outer')
    writer = pd.ExcelWriter(
        "Reports\\stores-sellers.xlsx", engine='xlsxwriter')
    autofit_and_save(writer, sellers_upd)
    sellers = sellers[['Κατάστημα', 'Επωνυμία', 'Πωλητής']]
    sellers.rename(columns={'Κατάστημα': 'SKR_Shop'}, inplace=True)

    # Create basic MAP Report table
    mergedData = pd.merge(mergedData, sellers, on='SKR_Shop', how='outer')
    mergedData.drop(['SKR_Title', 'URL'], axis=1, inplace=True)
    mergedData['SKR_Price'] = mergedData['SKR_Price'].astype(float)
    mergedData['Diff'] = mergedData.apply(lambda row: (
        row.loc['SKR_Price'] - row.loc['MAP']), axis=1).round(2)
    mergedData['Diff%'] = mergedData.apply(
        lambda row: (row.loc['SKR_Price'] - row.loc['MAP']) / row.loc['SKR_Price'] * 100, axis=1).round(1)
    mergedData.rename(columns={'SKR_Price': 'Τιμή', 'SKR_Shop': 'Κατάστημα', 'Official_Seller': 'Επίσημος Μεταπωλητής','Product': 'Προϊόν', 'Category': 'Κατηγορία'}, inplace=True)

    # Create the files
    mergedDataChris = mergedData[
        ['Κατηγορία', 'SKU', 'Προϊόν', 'Κατάστημα', 'Επωνυμία', 'Τιμή', 'MAP', 'Diff', 'Diff%', 'Επίσημος Μεταπωλητής','Πωλητής']]
    mergedDataChris.sort_values(by=['Κατηγορία', 'Προϊόν', 'Τιμή'], inplace=True)
    writer = pd.ExcelWriter("Reports\\MAP-Report-SKU.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, mergedDataChris)

    mergedData = mergedData[
        ['Κατηγορία', 'Προϊόν', 'Κατάστημα', 'Επωνυμία', 'Τιμή', 'MAP', 'Diff', 'Diff%', 'Επίσημος Μεταπωλητής','Πωλητής']]
    mergedData.sort_values(by=['Κατηγορία', 'Προϊόν', 'Τιμή'], inplace=True)
    writer = pd.ExcelWriter("Reports\\MAP-Report.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, mergedData)

    only_below = mergedData.loc[mergedData['Diff'] < 0]
    only_below.sort_values(by=['Κατάστημα', 'Κατηγορία', 'Προϊόν'], inplace=True)
    writer = pd.ExcelWriter("Reports\\MAP_only_below.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, only_below)

    foutsitzis = only_below.loc[only_below['Πωλητής'] == 'Φουτσιτζής']
    writer = pd.ExcelWriter("Reports\\MAP_Foutsitzis.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, foutsitzis)

    a_Chatz = only_below.loc[only_below['Πωλητής'] == 'Α. Χατζηκυριακίδης']
    writer = pd.ExcelWriter("Reports\\MAP_A_Chatz.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, a_Chatz)

    xorianopoulos = only_below.loc[only_below['Πωλητής'] == 'Χωριανόπουλος']
    writer = pd.ExcelWriter("Reports\\MAP_Xorianopoulos.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, xorianopoulos)

    kolomvos = only_below.loc[only_below['Πωλητής'] == 'Κολόμβος']
    writer = pd.ExcelWriter("Reports\\MAP_Kolomvos.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, kolomvos)

    vasiliadis = only_below.loc[only_below['Πωλητής'] == 'Βασιλειάδης']
    writer = pd.ExcelWriter("Reports\\MAP_Vasiliadis.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, vasiliadis)

    sttoulis = only_below.loc[only_below['Πωλητής'] == 'Σ. Τουλής']
    writer = pd.ExcelWriter("Reports\\MAP_St_Toulis.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, sttoulis)

    ctoulis = only_below.loc[only_below['Πωλητής'] == 'Χ. Τουλής']
    writer = pd.ExcelWriter("Reports\\MAP_C_Toulis.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, ctoulis)

    hatzikiriakidis = only_below.loc[only_below['Πωλητής'] == 'Χατζηκυριακίδης']
    writer = pd.ExcelWriter("Reports\\MAP_Hatzikiriakidis.xlsx", engine='xlsxwriter')
    autofit_colour_and_save(writer, hatzikiriakidis)

    fileNames_Admin = ['MAP-Report.xlsx', 'MAP_only_below.xlsx']
    # fileNames_Admin = ['MAP-Report.xlsx', 'MAP_only_below.xlsx', 'debug.log']
    fileNames_Christoforos = ['MAP-Report-SKU.xlsx', 'MAP-products.xlsx']
    fileNames_Michou = ['MAP-Report.xlsx', 'MAP_only_below.xlsx', 'MAP-products.xlsx', 'MAP-Report-SKU.xlsx']
    fileNames_Alexandridou = ['MAP-Report.xlsx', 'MAP_only_below.xlsx']
    fileNames_Foutsitzis = ['MAP-Report.xlsx', 'MAP_Foutsitzis.xlsx']
    fileNames_A_Chatz = ['MAP-Report.xlsx', 'MAP_A_Chatz.xlsx']
    fileNames_Xorianopoulos = ['MAP-Report.xlsx', 'MAP_Xorianopoulos.xlsx']
    fileNames_Kolomvos = ['MAP-Report.xlsx', 'MAP_Kolomvos.xlsx']
    fileNames_Vasiliadis = ['MAP-Report.xlsx', 'MAP_Vasiliadis.xlsx']
    fileNames_St_Toulis = ['MAP-Report.xlsx', 'MAP_St_Toulis.xlsx', 'MAP_only_below.xlsx', 'MAP-products.xlsx']
    fileNames_C_Toulis = ['MAP-Report.xlsx','MAP_C_Toulis.xlsx', 'MAP_only_below.xlsx']
    fileNames_Hatzikiriakidis = ['MAP-Report.xlsx', 'MAP_Hatzikiriakidis.xlsx', 'MAP_C_Toulis.xlsx', 'MAP_St_Toulis.xlsx', 'MAP_Vasiliadis.xlsx', 'MAP_Kolomvos.xlsx', 'MAP_Xorianopoulos.xlsx', 'MAP_A_Chatz.xlsx', 'MAP_Foutsitzis.xlsx', 'MAP_only_below.xlsx']
    fileNames_Xristina = ['MAP-Report.xlsx', 'MAP_only_below.xlsx']

    todayDate = datetime.today().strftime('%d-%m-%Y')
    time_needed = datetime.now() - startTime
    time_needed = str(time_needed)

    send_mail('e.vakalis@soundstar.gr', 'STAGING Skroutz MAP Report ' + todayDate,
                'Skroutz price report for our MAP products. Time to complete: ' + time_needed, fileNames_Admin)
    # send_mail('sales@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Christoforos)
    # send_mail('a.michou@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Michou)
    # send_mail('m.alexandridou@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Alexandridou)
    # send_mail('i.foutsitzis@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Foutsitzis)
    # send_mail('akritas.chatz@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_A_Chatz)
    # send_mail('k.horianopoulos@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Xorianopoulos)
    # send_mail('g.kolomvos@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Kolomvos)
    # send_mail('th.vasiliadis@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Vasiliadis)
    # send_mail('st.toulis@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_St_Toulis)
    # send_mail('c.toulis@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_C_Toulis)
    # send_mail('minas.hatz@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Hatzikiriakidis)
    # send_mail('xristinaxatz@soundstar.gr', 'Skroutz MAP Report ' + todayDate, 'Skroutz price report for our MAP products', fileNames_Xristina)