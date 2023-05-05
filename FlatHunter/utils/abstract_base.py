from bs4 import BeautifulSoup
import requests
from pathlib import Path
from requests.exceptions import HTTPError
from FlatHunter.utils.logging_utils import logger
from FlatHunter.utils.misc_utils import getPath
import pickle
from datetime import datetime
from abc import ABC, abstractmethod

ROOT_PATH = getPath("root")
PROJECT_PATH = getPath("project")

class FlatHunterBase(ABC):
    def __init__(self, itemCategory):
        """
        Item category can be either "flat", "industrial", "commercial" or "office". This constructor should be called by children classes
        and construct a dictionary containing all necessary URLs for each type of item category.
        """
        self.itemCategory = itemCategory

    @abstractmethod
    def searchPages(self):
        """
        This method should extract individual ads pages thanks to `getNumberOfPages()` and `getPageSoup()` methods in a loop to go through all pages in search.
        Finally, it sends individual page's soup to getAds() to extract all page's ads and place them in a list. This ads list returned by getAds() is 
        then placed in a list of lists, each list containing ads from a single page.
        """
        pass

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

    def getPageSoup(self, _url):
        """
        Handle HTTP requests/response and get page's soup.

        Params
        ------
        _url : string
            URL of page.
        """
        # User-Agent to avoid being rejected by website
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
        }
        try:
            response = requests.get(_url, headers=headers)
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")  # Python 3.6
            raise HTTPError(f"HTTP error occurred : {http_err}")
        except Exception as err:
            logger.error(f"Other error occurred: {err}")  # Python 3.6
            raise Exception(f"Other error occurred : {err}")
        else:
            logger.info(f"Succssfully connected to {_url}")
            # Return page's soup
            return BeautifulSoup(response.content, "html.parser")

    def dumpSoupHtml(self, soup, filename):
        """
        Dump soup's html to a file. For debugging purposes.

        Params
        ------
        soup : bs4.BeautifulSoup
            Soup to dump.
        filename : string
            Name of file to dump soup's html to.
        """
        with open(f"{PROJECT_PATH}/tests/pageDump/{filename}.html", "w") as file:
            file.write(soup.prettify())
    
    @staticmethod
    def getElementsByClass(soup, get="all", _class=""):
        """
        Get one or multiple elements by class. Used to standardize the way elements are searched in a soup, handle errors and avoid repetition.

        Parameters
        ----------
        soup : bs4.BeautifulSoup 
            Soup of page to search in.
        get : string
            Either "all" or "first". "all" will return all elements matching the class, "first" will return the first element matching the class.
        _class : string
            Class to search for.

        Returns
        -------
        list
            List of all elements matching the class (or None).
        bs4.element.Tag
            First element matching the class (or None).
        """
        if get == "all":
            try:
                listOfElements = soup.find_all(class_=_class)
            except Exception as e:
                logger.error(e)
                return None
            else:
                if listOfElements == []:
                    logger.warning(f"No elements with class name '{_class}' found in soup !")
                    return None
                return listOfElements
        elif get == "first":
            try:
                element = soup.find(class_=_class)
            except Exception as e:
                logger.error(e)
                return None
            else:
                if element == None:
                    logger.warning(f"No element with class name '{_class}' found !")
                    return None
                return element
        else:
            raise ValueError("Param 'get' must be either 'all' or 'first'")

    @staticmethod
    def saveObject(obj, filePrefix, test=False):
        """
        Save object to a file for later use. Object saved is a dictionnary containing
        saved object and a timestamp (datetime object), key names are `object` and `timestamp`.
        """
        savedDict = {}
        # Save timestamp & object
        savedDict["timeStamp"] = datetime.now()
        savedDict["object"] = obj
        folder = Path(f"{ROOT_PATH}/data/output")
        # Save object & timeStamp
        filename = f"{folder}/{filePrefix}_{datetime.now().strftime('%d-%m-%y_%H:%M:%S')}.search"
        if test==True:
            filename = f"{folder}/{filePrefix}"
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
        print(f"{ROOT_PATH}/data/output/{filename}")
        try:
            with open(f"{ROOT_PATH}/data/output/{filename}", "rb") as f:
                return pickle.load(f)
        except Exception as ex:
            print("Error during unpickling object (Possibly unsupported):", ex)
