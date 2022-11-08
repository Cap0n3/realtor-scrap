from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
import re
from utils.logUtil import logger
import pickle
from datetime import datetime

class BaseImmoCH:
    def __init__(self, itemToSearch):
        self.URLs = {
            "website" : "https://www.immobilier.ch",
            "flats" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/", "params" : "?t=rent&c=1;2&p=s40&nb=false&gr=1"},
            "industrial" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/industriel/geneve/", "params" : "?t=rent&c=7&p=s40&nb=false&gr=2"},
            "commercial" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/commercial/geneve/", "params" : "?t=rent&c=4&p=s40&nb=false"}
        }
        self.itemToSearch = itemToSearch

    def getPageSoup(self, _url):
        """
        Handle HTTP requests/response and get page's soup.

        Params
        ------
        _url : string
            URL of page.
        """
        # User-Agent to avoid being rejected by website
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        try:
            response = requests.get(_url, headers=headers)
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}") # Python 3.6
        except Exception as err:
            logger.error(f"Other error occurred: {err}") # Python 3.6
        else:
            logger.info(f"Succssfully connected to {_url}")
            # Return page's soup
            return BeautifulSoup(response.content, "html.parser")
    
    def getNumberOfPages(self, _soup):
        """
        Find total number of pages in any given immobilier.ch search.

        Params
        ------
        _soup : <class bs4>
            BS4 soup of first search page.

        Return
        ------
        lastPageNumber : int
            Number representing last page of search.
        """
        # Find pagination list
        try:
            paginationList = _soup.find("ul", "pages")
        except Exception as e:
            print(f"ERROR : Pagination not found on page ! Error message : {e}")
        else:    
            # Get list items
            liList = paginationList.find_all("li")
            # Get last list item (last page number)
            lastPageNumber = int(liList[-1].get_text())
            return lastPageNumber

    def getAds(self, _soup):
        """
        Extract ad main elements, basically it'll extract ad data-id and link along with its two main elements 
        `filter-content` and `filter-item-characteristic` soup that contains all important data concerning the good 
        (no matter if it's flat, industrial or commercial).
        
        Params
        ------
        _soup : <class bs4>
            Page soup containing all the ads

        Returns
        -------
        adsDictList : list
            List containing dictionnaries (representing each ads) with keys :
                <data-id> int : ID of ad
                <link> str : Link of ad
                <content-soup> class : Soup of `filter-content` tag
                <character-soup> class : Soup of `filter-item-characteristic` tag
        """
        adsDictList = []
        # Get all individual ads in a list
        allAdItems = _soup.find_all(class_="filter-item")
        # Extract container content
        for item in allAdItems:
            itemDict = {}
            # Extract data-id from container
            try:
                dataID = item['data-id']
            except KeyError:
                itemDict["data-id"] = None
                logger.warn(f"No data-id for item (KeyError) : {item}")
            else:
                itemDict["data-id"] = int(dataID)
                logger.debug(f"Extracting item with data-id {dataID}")
            # Get ad container (item link and all infos about link)
            adContainer = item.find(class_="filter-item-container")
            # Extract item link from container
            try:
                link = adContainer.find(id=f"link-result-item-{dataID}")
            except KeyError:
                itemDict["link"] = None
                logger.warn(f"No link for item with data-id {dataID} : KeyError")
            else:
                if link != None:
                    itemDict["link"] = self.URLs["website"] + link["href"]
            # Get ad content (name, price, address, etc...)
            adContent = adContainer.find(class_="filter-item-content")
            itemDict["content-soup"] = adContent
            # Get ad characteristics (Size, rooms, etc...)
            adCharacter = adContainer.find(class_="filter-item-characteristic")
            itemDict["character-soup"] = adCharacter
            # Push dictionnary in list
            adsDictList.append(itemDict)
            logger.debug(f"Added new dictionnary in list : {itemDict}")
        # Return all ads
        return adsDictList

    def searchPages(self, searchPages=None):
        """
        Method that loop through pages and extract all ads informations.

        Params
        ------
        searchPages : int
            How many pages should be searched. If left empty, it'll search all available pages.

        Returns
        -------
        pagesList : list
            List of lists containing dictionnaries representing ads. Each nested list is a page and dictionnaries inside are individual ad.
        """
        # Define type of search and create associated URL
        if self.itemToSearch == "flat":
            baseURL = self.URLs["flats"]["mainURL"]
            params = self.URLs["flats"]["params"]
        elif self.itemToSearch == "industrial":
            baseURL = self.URLs["industrial"]["mainURL"]
            params = self.URLs["industrial"]["params"]
        elif self.itemToSearch == "commercial":
            baseURL = self.URLs["commercial"]["mainURL"]
            params = self.URLs["commercial"]["params"]
        else:
            raise AttributeError("Wrong attribute ! Attribute can be either 'flat', 'industrial' and 'commercial'")
        # Get total number of pages for given search (go to first page of search)
        # URL should look like this : "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/page-1?t=rent&c=1;2&p=s40&nb=false&gr=1"
        firstPageURL = f"{baseURL}page-1{params}"
        logger.info(f"Extract number of pages from following URL : '{firstPageURL}'")
        soup = self.getPageSoup(firstPageURL)
        numberOfPages = self.getNumberOfPages(soup)
        logger.info(f"Total number of pages for search is {numberOfPages}")
        # Establish connexion with all individual pages (loop)
        if searchPages != None:
            # If user specified an exact number of page to search
            numberOfPages = searchPages
        pagesList = [] # List of list containing dictionnaries representing ads
        for pageNb in range(1, numberOfPages + 1):
            pageURL = f"{baseURL}page-{pageNb}{params}"
            logger.info(f"Get soup from URL : '{pageURL}'")
            pageSoup = self.getPageSoup(pageURL)
            # Extract individual ad infos
            adsList= self.getAds(pageSoup)
            logger.info(f"<====== Extracted ads of page {pageNb} ======>")
            logger.debug(f"List of extracted ads dict : {adsList}")
            pagesList.append(adsList)
        return pagesList

# =========================== #
# ====== QUICK TESTING ====== #
# =========================== #
obj = BaseImmoCH("flat")
obj.searchPages(1)