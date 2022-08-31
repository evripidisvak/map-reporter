from django.core.management.base import BaseCommand, CommandError
from django.db import models
import os
import pandas as pd
from reporter.models import *


class Command(BaseCommand):
    help = "Import sellers in shops"

    def handle(self, *args, **options):
        current_folder = os.getcwd()
        shops_csv = pd.read_csv(
            current_folder + "/reporter/management/commands/stores-sellersCOPY.csv"
        )

        shops_csv.drop_duplicates("shop", inplace=True)
        shops_csv.dropna(subset="email", inplace=True)

        # print(shops_csv.head())
        shop_db = Shop.objects.filter(name__in=shops_csv["shop"])

        for shop in shop_db:
            row = shops_csv.loc[shops_csv["shop"] == shop.name].copy()
            seller_email = row["email"].values[0]
            try:
                seller = User.objects.get(email=seller_email)
                shop.seller = seller
                shop.save()
            except:
                print(seller_email)
