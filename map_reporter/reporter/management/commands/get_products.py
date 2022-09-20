from django.core.management.base import BaseCommand, CommandError
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from woocommerce import API
import os
import pandas as pd
from reporter.models import *
from decimal import *

class Command(BaseCommand):
    help = 'Gets all products with bottom price'

    def handle(self, *args, **options):
        # try:
            wcapi = API(
                url="https://soundstar.gr/",
                consumer_key="ck_80837502abc4a1151d99d09292234a859034a3ad",
                consumer_secret="cs_a7b8eefeeb54db775fc651e6dab141d9e5b7f0b5",
                timeout=50
            )
            current_folder = os.getcwd()
            map_products = pd.read_csv(current_folder + '/reporter/management/commands/map-products-api.csv')

            for index, row in map_products.iterrows():
                product = wcapi.get('products/?sku='+row['SKU']).json()
                attributes = product[0]['attributes']
                meta_data = product[0]['meta_data']
                image_url = product[0]['images'][0]['src']
                sku = row['SKU']
                category = Category.objects.get(name=str(row['Category']))
                for attribute in attributes:
                    if attribute['name'] == 'Manufacturer':
                        manufacturer = attribute['options'][0].capitalize()
                        if manufacturer == 'First':
                            manufacturer = 'First Austria'
                        manufacturer_obj, created = Manufacturer.objects.get_or_create(name=str(manufacturer))
                    if attribute['name'] == 'Model':
                        model = attribute['options'][0]
                for data in meta_data:
                    if data['key'] == '_b_price':
                        print(sku)
                        print(data['value'])
                        if data['value']:
                            map_price = "{:.2f}".format(float(data['value']))
                        else:
                            map_price = 1
                        break

                product = Product.objects.create(manufacturer=manufacturer_obj, model=model, sku=sku, active=True, map_price=map_price, main_category=category, image_url=image_url)
                if row['Skroutz']:
                    if not pd.isnull(row['Skroutz']):
                        Page.objects.get_or_create(url=row['Skroutz'], product=product, source=Source.objects.get(name='Skroutz'))
                if row['Electronet']:
                    if not pd.isnull(row['Electronet']):
                        Page.objects.get_or_create(url=row['Electronet'], product=product, source=Source.objects.get(name='Electronet'))
                if row['Germanos']:
                    if not pd.isnull(row['Germanos']):
                        Page.objects.get_or_create(url=row['Germanos'], product=product, source=Source.objects.get(name='Germanos'))
                # if row['Media Markt']:
                #     if not pd.isnull(row['Media Markt']):
                #         Page.objects.get_or_create(url=row['Media Markt'], product=product, source=Source.objects.get(name='Media Markt'))
                if row['You']:
                    if not pd.isnull(row['You']):
                        Page.objects.get_or_create(url=row['You'], product=product, source=Source.objects.get(name='You'))
                if row['Public']:
                    if not pd.isnull(row['Public']):
                        Page.objects.get_or_create(url=row['Public'], product=product, source=Source.objects.get(name='Public'))
                if row['Kotsovolos']:
                    if not pd.isnull(row['Kotsovolos']):
                        Page.objects.get_or_create(url=row['Kotsovolos'], product=product, source=Source.objects.get(name='Kotsovolos'))
                if row['Praktiker']:
                    if not pd.isnull(row['Praktiker']):
                        Page.objects.get_or_create(url=row['Praktiker'], product=product, source=Source.objects.get(name='Praktiker'))
                if row['Plaisio']:
                    if not pd.isnull(row['Plaisio']):
                        Page.objects.get_or_create(url=row['Plaisio'], product=product, source=Source.objects.get(name='Plaisio'))
        # except:
            # pass
