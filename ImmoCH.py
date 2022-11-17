from bs4 import BeautifulSoup
import requests
from pathlib import Path
from requests.exceptions import HTTPError
import re
from utils.logUtil import logger
import pickle
from datetime import datetime
from abc import ABC, abstractmethod


CURR_PATH = Path(__file__).parent.absolute()

class RealtorScrap(ABC):
    def __init__(self, itemCategory):
        """
        Item category can be either "flat", "industrial", "commercial" or "office".
        """
        self.itemCategory = itemCategory

    @staticmethod
    def saveObject(obj, filePrefix):
        """
        Save object to a file for later analyse. Object saved is a dictionnary containing
        saved object and a timestamp (datetime object), key names are `object` and `timestamp`.
        """
        savedDict = {}
        # Save timestamp & object
        savedDict["timeStamp"] = datetime.now()
        savedDict["object"] = obj
        # Check if folder exists & create if doesn't exist
        folder = Path(f"{CURR_PATH}/savedResults")
        if not folder.exists():
            Path("savedResults").mkdir(parents=True, exist_ok=True)
        # Save object & timeStamp
        filename = f"savedResults/{filePrefix}_{datetime.now().strftime('%d-%m-%y_%H:%M:%S')}.search"
        print(savedDict)
        try:
            with open(filename, "wb") as f:
                pickle.dump(savedDict, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("Error during pickling object (Possibly unsupported):", e)
    
    @staticmethod
    def loadObject(filename):
        """
        Load pickle object.
        """
        print(f"{CURR_PATH}/savedResults/{filename}")
        try:
            with open(f"{CURR_PATH}/savedResults/{filename}", "rb") as f:
                return pickle.load(f)
        except Exception as ex:
            print("Error during unpickling object (Possibly unsupported):", ex)
    
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
        
    @abstractmethod
    def getNumberOfPages(self):
        """
        Find total number of pages in any given search.
        """
        pass
    
    @abstractmethod
    def getAds(self):
        """
        This method should be in charge of extracting ads informations in any given page's soup. Those informations should not be 
        too refined (yet) and be populated in a dictionnay which in turn will be placed in a list of dictionnaries.
        """
        pass
    
    @abstractmethod
    def searchPages(self):
        """
        It should be the main method of children classes. It defines all necessary URLs for 'flat', 'industrial', 'commercial' and 'office' and
        then extract individual ads pages thanks to `getNumberOfPages()` and `getPageSoup()` in a loop to go through all pages in search. 
        Finally, it sends individual page's soup to getAds() to extract all page's ads and place them in a list.
        """
        pass
    
    @abstractmethod
    def getItems(self):
        """
        This method is responsible for sorting the data according to user-defined filters and the total number of pages to be searched.
        It would call searchPages() method, retrieve list containing all unrefined and unfiltered assets and extract all relevant infos
        from ad soup. This method should contain nested functions that will extract information in a specific manner according to the
        type of informations that should be extracted (flat, industrial, commercial, office).
        """
        pass

class ImmoCH(RealtorScrap):
    def __init__(self, itemCategory):
        self.URLs = {
            "website" : "https://www.immobilier.ch",
            "flats" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/", "params" : "?t=rent&c=1;2&p=s40&nb=false&gr=1"},
            "industrial" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/industriel/geneve/", "params" : "?t=rent&c=7&p=s40&nb=false&gr=2"},
            "commercial" : { "mainURL" : "https://www.immobilier.ch/fr/carte/louer/commercial/geneve/", "params" : "?t=rent&c=4&p=s40&nb=false"}
        }
        super().__init__(itemCategory)
    
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
        Extract ad main elements, basically it'll extract ad `data-id` and `link` along with its three main elements 
        `filter-content`, `filter-item-characteristic` and item `container` div soup that contains all important data concerning 
        the good (no matter if it's flat, industrial or commercial).
        
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
                <ad-content-soup> class : Soup of `filter-content` tag (name, price, address, etc...)
                <ad-character-soup> class : Soup of `filter-item-characteristic` tag (Size, rooms, etc...)
                <item-page-soup> class : Soup of item's page `container` tag 
        """
        adsDictList = []
        # Get all individual ads in a list
        allAdItems = _soup.find_all(class_="filter-item")
        # Extract container content
        for item in allAdItems:
            itemDict = {}
            # == Extract data-id from container == #
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
            # == Extract item link from container == #
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
            itemDict["ad-content-soup"] = adContent
            # Get ad characteristics (Size, rooms, etc...)
            adCharacter = adContainer.find(class_="filter-item-characteristic")
            itemDict["ad-character-soup"] = adCharacter
            # == Go to page and scrap item full page == #
            if link != None:
                logger.debug(f"Trying connection to item's page at URL : {itemDict['link']}")
                pageItemSoup = self.getPageSoup(itemDict["link"])
                try:
                    itemContainer = pageItemSoup.find(class_="container--large")
                except Exception as e:
                    logger.warn(f"Couldn't find item's container in item's page (item {dataID})")
                else:
                    itemDict["item-page-soup"] = itemContainer
                    logger.info(f"Item page's soup successfully extracted for item with id {dataID}")
            else:
                logger.warn(f"Couldn't reach item's page, no link extracted for item with id {dataID}")
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
        # == Define type of search and create associated URL == #
        if self.itemCategory == "flat":
            baseURL = self.URLs["flats"]["mainURL"]
            params = self.URLs["flats"]["params"]
        elif self.itemCategory == "industrial":
            baseURL = self.URLs["industrial"]["mainURL"]
            params = self.URLs["industrial"]["params"]
        elif self.itemCategory == "commercial":
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
        # == Establish connexion with all individual pages (loop) == #
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
        # ====== Save list ====== #
        ImmoCH.saveObject(pagesList, "immoCH")
        # ====== Return list ====== #
        return pagesList

    def getItems(self, filter, totalPages=None, fileName=None):
        """
        This method is responsible for sorting the data according to user-defined filters and the total number of pages to be searched.
        Note : See abstract class docString for more infos.

        Params
        ------
        filter : dict
            Dictionnary with "minRent", "maxRent", "minSize", "maxSize", "minRooms" (only for flat search) and "maxRooms" (only for flat search) 
            keys.
        totalPages : int
            Total number of page to seach on website.
        fileName : str
            Give a `.search` file type to get and filter its content (files are automatically created after a search).
        """
        # ================================== #
        # ========= CORE FUNCTIONS ========= #
        # ================================== #
        def getRent(category, adData):
            if category == "flat":
                try:
                    contentDiv = ad["ad-content-soup"].find(class_="filter-item-content")
                except AttributeError:
                    logger.warn(f"ad['ad-content-soup'] is equal to None ! Couldn't extract rent from item ID {ad['data-id']}")
                else:
                    if contentDiv != None:
                        rawRent = re.sub("'", "", contentDiv.find(class_="title").get_text())
                        logger.debug(re.search(r"CHF\s\d+\.-/mois", rawRent))
        
        # ======================== #
        # ========= MAIN ========= #
        # ======================== #
        # === CHECK filter dict keys : If flat is selected, must also have rooms indicated === #
        if self.itemCategory == "flat":
            try:
                filter["minRooms"] and filter["maxRooms"]
            except KeyError:
                print("ERROR : You must indicate 'minRooms' and 'maxRooms' for an appartement search.")
                logger.error("User didn't indicate 'minRooms' and 'maxRooms' for an appartement search in filter dict. Stopped script.")
        
        # === Lauch search OR load object from file === #
        if fileName != None:            
            # pathlist = Path(f"{CURR_PATH}/savedResults").glob('*')
            # for path in pathlist:
            #     if path.name == fileName:
            #         loadedObj = ImmoCH.loadObject(path)
            #         allAdsList = loadedObj.object
            
            loadedObj = ImmoCH.loadObject(fileName)
            print(loadedObj)
        else:
            # If no file name is provided, just lauch a new search
            allAdsList = self.searchPages(totalPages)
        
        # === Main loop === #
        for page in allAdsList:
            for ad in page:
                # == Get rent == #
                rent = getRent(self.itemCategory, ad)

        # == Get rent == #
        
# =========================== #
# ====== QUICK TESTING ====== #
# =========================== #
obj = ImmoCH("flat")
filterParams = {
    "minRent" : 1000,
    "maxRent" : 1900,
    "minSize" : 45,
    "maxSize" : 80,
    "minRooms" : 3.5,
    "maxRooms" : 4
}
obj.getItems(filterParams, totalPages=1)
