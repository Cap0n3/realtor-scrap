"""
This file is used to make quick local test with bs4 queries.
"""

from bs4 import BeautifulSoup
import requests
from FlatHunter.utils.misc_utils import getPath
from FlatHunter.utils.abstract_base import FlatHunterBase

PROJECT_PATH = getPath("project")

# Define path to page to test
AD_PAGE_PATH = f"{PROJECT_PATH}/tests/LocalQueryTests/PagesToQuery/ad_page.html"

# === Open local page === #
with open(AD_PAGE_PATH) as fp:
    localPageSoup = BeautifulSoup(fp, 'html.parser')

# === Open remote page === #
# Bogus class just to get page soup
class Bogus(FlatHunterBase):
    def __init__(self):
        pass

    def getNumberOfPages(self):
        pass

    def getAds(self):
        pass

    def searchPages(self):
        pass
    
    def getItems(self):
        pass

obj = Bogus()
URL = "https://www.immobilier.ch/fr/louer/appartement/geneve/geneve/grange-cie-34/chemin-roches-15-898645"
webPageSoup = obj.getPageSoup(URL)

# === Simple test queries === #
#print(webPageSoup)
print(obj.getElementsByClass(webPageSoup, get="all", _class="im__col--postContent"))