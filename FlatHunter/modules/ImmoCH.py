import re
from FlatHunter.utils.abstract_base import FlatHunterBase
from FlatHunter.utils.logging_utils import logger


class ImmoCH(FlatHunterBase):
    def __init__(self, itemCategory):
        self.URLs = {
            "website": "https://www.immobilier.ch",
            "flats": {
                "mainURL": "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/",
                "params": "?t=rent&c=1;2&p=s40&nb=false&gr=1",
            },
            "industrial": {
                "mainURL": "https://www.immobilier.ch/fr/carte/louer/industriel/geneve/",
                "params": "?t=rent&c=7&p=s40&nb=false&gr=2",
            },
            "commercial": {
                "mainURL": "https://www.immobilier.ch/fr/carte/louer/commercial/geneve/",
                "params": "?t=rent&c=4&p=s40&nb=false",
            },
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
                <ad-page-soup> class : Soup of item's page `container` tag
        """
        adsDictList = []
        # Get all individual ads in a list
        allAdItems = _soup.find_all(class_="filter-item")
        # Extract container content
        for item in allAdItems:
            itemDict = {}
            # == Extract data-id from container == #
            try:
                dataID = item["data-id"]
            except KeyError:
                itemDict["data-id"] = None
                logger.warning(f"No data-id for item (KeyError) : {item}")
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
                logger.warning(f"No link for item with data-id {dataID} : KeyError")
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
                logger.debug(
                    f"Trying connection to item's page at URL : {itemDict['link']}"
                )
                pageItemSoup = self.getPageSoup(itemDict["link"])
                try:
                    itemContainer = pageItemSoup.find(id="main")
                except Exception as e:
                    logger.warning(
                        f"Couldn't find item's container in item's page (item {dataID})"
                    )
                else:
                    itemDict["ad-page-soup"] = itemContainer
                    logger.info(
                        f"Item page's soup successfully extracted for item with id {dataID}"
                    )
            else:
                logger.warning(
                    f"Couldn't reach item's page, no link extracted for item with id {dataID}"
                )
            # Push dictionnary in list
            adsDictList.append(itemDict)
            logger.debug(f"Added new dictionnary in list : {itemDict}")
        # Return all ads
        return adsDictList

    def searchPages(self, pagesToSearch=None):
        """
        Method that loop through pages and extract all ads.

        Params
        ------
        pagesToSearch : int
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
            raise AttributeError(
                "Wrong attribute ! Attribute can be either 'flat', 'industrial' and 'commercial'"
            )
        # Get total number of pages for given search (go to first page of search)
        # URL should look like this : "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/page-1?t=rent&c=1;2&p=s40&nb=false&gr=1"
        firstPageURL = f"{baseURL}page-1{params}"
        logger.info(f"Extract number of pages from following URL : '{firstPageURL}'")
        soup = self.getPageSoup(firstPageURL)
        numberOfPages = self.getNumberOfPages(soup)
        logger.info(f"Total number of pages for search is {numberOfPages}")
        # == Establish connexion with all individual pages (loop) == #
        if pagesToSearch != None:
            # If user specified an exact number of page to search
            numberOfPages = pagesToSearch
        pagesList = []  # List of list containing dictionnaries representing ads
        for pageNb in range(1, numberOfPages + 1):
            pageURL = f"{baseURL}page-{pageNb}{params}"
            logger.info(f"Get soup from URL : '{pageURL}'")
            pageSoup = self.getPageSoup(pageURL)
            # Extract individual ad infos
            adsList = self.getAds(pageSoup)
            logger.info(f"<====== Extracted ads of page {pageNb} ======>")
            logger.info(f"Total ads extracted : {len(adsList)}")
            logger.debug(f"List of extracted ads dict : {adsList}")
            pagesList.append(adsList)
        # ====== Return list ====== #
        return pagesList

    def getItems(self, filter, pagesToSearch=None):
        """
        This method is responsible for sorting the data according to user-defined filters and the total number of pages to be searched.
        Note : See abstract class docString for more infos.

        Params
        ------
        filter : dict
            Dictionnary with "minRent", "maxRent", "minSize", "maxSize", "minRooms" (only for flat search) and "maxRooms" (only for flat search)
            keys.
        pagesToSearch : int
            Total number of page to seach on website, if left empty it'll search all pages.
        
        Returns
        -------
        filteredAdsList : list
            List of dictionnaries containing all filtered ads.
        """
        # === CHECK filter dict keys : If flat is selected, must also have rooms indicated === #
        if self.itemCategory == "flat":
            try:
                filter["minRooms"] and filter["maxRooms"]
            except KeyError:
                print(
                    "ERROR : You must indicate 'minRooms' and 'maxRooms' for an appartement search."
                )
                logger.error(
                    "User didn't indicate 'minRooms' and 'maxRooms' for an appartement search in filter dict. Stopped script."
                )

        # Get list of ads (Nested list, each list is a page)
        allAdsList = self.searchPages(pagesToSearch)

        # Create list of dictionnaries containing all filtered ads
        filteredAdsList = []

        # === Main loop === #
        for page in allAdsList:
            for ad in page:
                formatedDict = {}
                # == Get rent == #
                rent = self._getRentHelper(self.itemCategory, ad)
                # == Get rooms == #
                rooms = self._getRoomsHelper(self.itemCategory, ad)
                # == Get size == #
                size = self._getSizeHelper(self.itemCategory, ad)
                images = self._getImagesHelper(self.itemCategory, ad)
                # Check if ad is a match with filter dict keys (rent, room, size) and add it to filteredAdsList if it is
                if rent >= filter["minRent"] and rent <= filter["maxRent"]:
                    if rooms >= filter["minRooms"] and rooms <= filter["maxRooms"]:
                        if size >= filter["minSize"] and size <= filter["maxSize"]:
                            logger.info(
                                f"Ad {ad['data-id']} is a match => {rooms} rooms, rent {rent} CHF and size {size} m2."
                            )
                            
                            formatedDict["data-id"] = ad["data-id"]
                            formatedDict["link"] = ad["link"]
                            formatedDict["images"] = images
                            formatedDict["rent"] = rent
                            formatedDict["rooms"] = rooms
                            formatedDict["size"] = size
                            # Add formated dict to filteredAdsList
                            filteredAdsList.append(formatedDict)

        # Return filtered ads list
        return filteredAdsList

    # === HELPER FUNCTIONS === #
    def _getRentHelper(self, category, adData):
        """
        getItem's helper function to extract rent from ad.
        """
        rent = None
        if category == "flat":
            try:
                contentDiv = adData["ad-content-soup"].find(class_="title")
            except AttributeError:
                logger.warning(
                    f"ad['ad-content-soup'] is equal to None ! Couldn't extract rent from item ID {adData['data-id']}"
                )
            else:
                if contentDiv != None:
                    rawRent = re.sub("'", "", contentDiv.get_text())
                    try:
                        rent = int(re.search(r"\d+", rawRent).group())
                    except AttributeError:
                        logger.warning(
                            f"Couldn't extract rent from item ID {adData['data-id']}"
                        )
                    else:
                        logger.debug(
                            f"Extracted rent for item with ID {adData['data-id']}. Item rent : {rent} CHF"
                        )

            return rent if rent != None else 0

    def _getRoomsHelper(self, category, adData):
        """
        getItem's helper function to extract rooms from ad.
        """
        rooms = None
        if category == "flat":
            try:
                contentDiv = adData["ad-content-soup"].find(class_="object-type")
            except AttributeError:
                logger.warning(
                    f"ad['ad-content-soup'] is equal to None ! Couldn't extract rent from item ID {adData['data-id']}"
                )
            else:
                if contentDiv != None:
                    rawRooms = contentDiv.get_text()
                    try:
                        rooms = float(re.search(r"\d+\.?\d?", rawRooms).group())
                    except AttributeError:
                        logger.warning(
                            f"Couldn't extract rooms from item ID {adData['data-id']}"
                        )
                    else:
                        logger.debug(
                            f"Extracted rent for item with ID {adData['data-id']}. Item rooms : {rooms}"
                        )

            return rooms if rooms != None else 0

    def _getSizeHelper(self, category, adData):
        """
        getItem's helper function to extract size from ad.
        """
        size = None
        if category == "flat":
            try:
                contentDiv = adData["ad-character-soup"].find(class_="space")    
            except AttributeError:
                logger.warning(
                    f"ad['ad-character-soup'] is equal to None ! Couldn't extract rent from item ID {adData['data-id']}"
                )
            else:
                if contentDiv != None:
                    rawSize = contentDiv.get_text()
                    
                    try:
                        size = int(re.search(r"\d+\.?\d?", rawSize).group())
                    except AttributeError:
                        logger.warning(
                            f"Couldn't extract size from item ID {adData['data-id']}"
                        )
                    else:
                        logger.debug(
                            f"Extracted rent for item with ID {adData['data-id']}. Item size : {size} m2"
                        )
            
            return size if size != None else 0
        
    def _getImagesHelper(self, category, adData):
        """
        getItem's helper function to extract images from ad.
        """
        try:
            imgBS4List = FlatHunterBase.getElementsByClass(adData["ad-page-soup"], get="all", _class="im__banner__slider")
        except KeyError:
            logger.warning(
                f"ad['ad-page-soup'] is equal to None ! Couldn't extract images from item ID {adData['data-id']}"
            )
        else:
            imgDict = {}
            if imgBS4List != None:
                imagesBS4List = imgBS4List[0].find_all("img")
                for image in imagesBS4List:
                    imgAlt = image["alt"]
                    images = image["data-lazy"]
                    imgDict[imgAlt] = images
            else:
                logger.warning(
                    f"Couldn't extract images from item ID {adData['data-id']}, 'im__banner__slider' is equal to None !"
                )  
            # Return dictionnary of images or empty dictionnary
            return imgDict