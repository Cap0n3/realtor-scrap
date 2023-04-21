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

# === Functions === #
# def getElementsByClass(soup, get="all", _class=""):
#     """
#     Get one or multiple elements by class.

#     Parameters
#     ----------
#     soup : bs4.BeautifulSoup 
#         Soup of page to search in.
#     get : string
#         Either "all" or "first". "all" will return all elements matching the class, "first" will return the first element matching the class.
#     _class : string
#         Class to search for.

#     Returns
#     -------
#     list
#         List of all elements matching the class.
#     bs4.element.Tag
#         First element matching the class.
#     """
#     if get == "all":
#         try:
#            listOfElements = soup.find_all(class_=_class)
#         except Exception as e:
#             print(e)
#             return None
#         else:
#             if listOfElements == []:
#                 print(f"No elements with class name '{_class}' found !")
#                 return None
#             return listOfElements
#     elif get == "first":
#         try:
#            element = soup.find(class_=_class)
#         except Exception as e:
#             print(e)
#             return None
#         else:
#             if element == None:
#                 print(f"No element with class name '{_class}' found !")
#                 return None
#             return element
#     else:
#         raise ValueError("Param 'get' must be either 'all' or 'first'")

# === Simple test queries === #
#print(webPageSoup)
print(obj.getElementsByClass(webPageSoup, get="all", _class="im__banner__slide"))