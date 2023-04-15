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

class FlatHunterBase(ABC):
    def __init__(self, itemCategory):
        """
        Item category can be either "flat", "industrial", "commercial" or "office".
        """
        self.itemCategory = itemCategory

    @staticmethod
    def saveObject(obj, filePrefix, test=False):
        """
        Save object to a file for later analysis. Object saved is a dictionnary containing
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
        except Exception as err:
            logger.error(f"Other error occurred: {err}")  # Python 3.6
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

        Note : This method is the one that user will call to get filtered information about ads.
        """
        pass