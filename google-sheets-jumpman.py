import gspread
from oauth2client.service_account import ServiceAccountCredentials

from woocommerce import API

import requests
from bs4 import BeautifulSoup

import re
from idlecolors import *

k = 42

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
gc = gspread.authorize(credentials)
wks = gc.open('Jumpman').worksheet('ART_jordan')

wcapi = API(
    url="https://jumpman.com.ua/",
    consumer_key="ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    consumer_secret="cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    timeout=50
)

URL = 'https://jumpman.com.ua/product-category/'

categories = [
    'clothings/',
    'shoes/',
    'accessories/',
]

VENDORS = {
    '?filters=ow[ital]': 'ital',
    '?filters=ow[jump]': 'jump',
    '?filters=ow[dan]': 'dan',
}
m = 0

for c in categories:
    for v in list(VENDORS.keys()):
        general_url = f"{URL}{c}{v}"

        req = requests.get(general_url)
        soup5 = BeautifulSoup(req.text, 'lxml')
        try:
            page_num = int(soup5.find('ul', class_='page-numbers').findAll('a')[-2].text)
        except AttributeError:
            page_num = 1

        for l in range(1, page_num):
            pages_url = f"{URL}{c}page/{l}/{v}"
            r = requests.get(pages_url)
            soup1 = BeautifulSoup(r.text, 'lxml')

            products = soup1.findAll('li', class_='product')
            for i in products:
                m += 1
                product_info = {}

                g = i.get('class')

                product_info['id'] = int(re.findall(r'post-([+]?\d+)', g[2])[0])
                product_info['url'] = i.find('a', class_='woocommerce-LoopProduct-link').get('href')

                request = requests.get(product_info['url'])
                soup = BeautifulSoup(request.text, 'lxml')
                o = soup.find('span', class_='sku').text
                for s in ['-d', '-j', '-it']:
                    if s in o:
                        o = o.replace(s, '')
                product_info['sku'] = o
                table = wks.findall(product_info['sku'])
                for j in table:
                    f = wks.row_values(j.row)
                    if f[8] == VENDORS[v] and int(f[11]) > 0:
                        product_info['price'] = float(re.findall(r' \$(.+)', f[19])[0].replace(',', '.'))
                        break
                d = wcapi.get(f"products/{product_info['id']}").json()['variations']
                try:
                    data = {
                        'regular_price': str(round(product_info['price'] * k))
                    }
                    print(f"#{m}: {product_info['sku']} {product_info['price']} - {round(product_info['price'] * k)}")

                    for j in d:
                        r = wcapi.put(f"products/{product_info['id']}/variations/{j}", data).json()
                except KeyError:
                    printc(red(f"#{m} - {product_info['sku']} - DONT SUCCES"))


