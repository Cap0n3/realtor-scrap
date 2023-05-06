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

    def getAds(self, _soup, filter=None):
        """
        Get all ads from a given page. Apply filters if any.

        Params
        ------
        _soup : <class bs4>
            BS4 soup of first search page.
        filter : dict
            Dictionary containing filters to apply to ads, if ommited, no filter is applied.

        Return
        ------
        adsDictList : list
            List of dictionnaries containing all ads informations.
        """
        adsDictList = []
        
        # Get all individual ads in a list
        allAdItems = FlatHunterBase.getElementsByClass(_soup, get="all", _class="filter-item")

        for ad in allAdItems:
            adDict = {}
            # == Extract data-id from container == #
            try:
                dataID = ad["data-id"]
            except KeyError:
                adDict["data-id"] = None
                dataID = 0
                logger.warning(f"No data-id for item (KeyError). Dumping content :\n {ad}")
            else:
                adDict["data-id"] = int(dataID)
                logger.debug(f"Extracting item with data-id {dataID}")
            # Get ad content (name, price, address, etc...), ad characteristics (Size, rooms, etc...) and ad container (link)
            adContent = FlatHunterBase.getElementsByClass(ad, get="first", _class="filter-item-content")
            adCaracteristics = FlatHunterBase.getElementsByClass(ad, get="first", _class="filter-item-characteristic")
            adContainer = FlatHunterBase.getElementsByClass(ad, get="first", _class="filter-item-container")
            # == Extract ad rent price == #
            rentStringBS4 = FlatHunterBase.getElementsByClass(adContent, get="first", _class="title")
            adDict["rent"] = self._formatRentStringHelper(dataID, rentStringBS4)
            # == Extract ad address == #
            adDict["address"] = self._getAddressHelper(dataID, adContent)
            # == Extract ad Rooms == #
            roomsStringBS4 = FlatHunterBase.getElementsByClass(adCaracteristics, get="first", _class="icon-plan")
            adDict["rooms"] = self._formatRoomsStringHelper(dataID, roomsStringBS4["title"] if roomsStringBS4 else None)
            # == Extract ad Size == #
            sizeStringBS4 = FlatHunterBase.getElementsByClass(adCaracteristics, get="first", _class="space")
            adDict["size"] = self._formatSizeStringHelper(dataID, sizeStringBS4)
            # == Extract item link from container == #
            adDict["link"] = self._getAdLinkHelper(dataID, adContainer)
            # == Apply filters or not == #
            if filter:
                if adDict["rent"] >= filter["minRent"] and adDict["rent"] <= filter["maxRent"]:
                        if adDict["rooms"] >= filter["minRooms"] and adDict["rooms"] <= filter["maxRooms"]:
                            if adDict["size"] >= filter["minSize"] and adDict["size"] <= filter["maxSize"]:
                                logger.info(
                                    f"Ad {ad['data-id']} is a match => {adDict['rooms']} rooms, rent {adDict['rent']} CHF and size {adDict['size']} m2."
                                )
                                adPageData = self.followAdLinkAndExtractData(adDict["data-id"], adDict["link"])
                                # merge both dictionnaries
                                adDict = {**adDict, **adPageData}
                                # Push dictionnary to list
                                adsDictList.append(adDict)
            elif not filter:
                logger.info(f"(No filters) Ad {ad['data-id']} => {adDict['rooms']} rooms, rent {adDict['rent']} CHF and size {adDict['size']} m2.")
                adPageData = self.followAdLinkAndExtractData(adDict["data-id"], adDict["link"])
                # merge both dictionnaries
                adDict = {**adDict, **adPageData}
                # Push dictionnary to list
                adsDictList.append(adDict)
        
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

    # === HELPER FUNCTIONS === #        
    def _getImagesHelper(self, dataID, adSoup):
        """
        getItem's helper function to extract images from ad.
        """
        imgDict = {}
        try:
            imgBS4List = FlatHunterBase.getElementsByClass(adSoup, get="all", _class="im__banner__slider")
        except KeyError:
            logger.warning(f"Couldn't extract images from item ID {dataID}, will return empty dictionnary !")
            logger.debug(f"Couldn't extract images from item ID {dataID} ! \nSoup dump : {adSoup}")

        else:
            if imgBS4List != None:
                imagesBS4List = imgBS4List[0].find_all("img")
                for image in imagesBS4List:
                    imgAlt = image["alt"]
                    images = image["data-lazy"]
                    imgDict[imgAlt] = images
            else:
                logger.warning(
                    f"Couldn't extract images from item ID {dataID}, 'im__banner__slider' is equal to None ! Will return empty dictionnary !"
                )  
        # Return dictionnary of images (or empty dictionnary)
        return imgDict

    def _formatRentStringHelper(self, dataID, rentString):
        """
        getAds's helper function to extract and format rent string.

        Params
        ------
        dataID : int
            Ad's data-id.
        rentString : bs4.element.Tag
            Ad's raw rent string.

        Returns
        -------
        rent : int
            Ad's rent.
        """
        rent = None
        if rentString != None:
            rawRent = re.sub("'", "", rentString.get_text())
            try:
                rent = int(re.search(r"\d+", rawRent).group())
            except AttributeError:
                logger.warning(
                    f"Couldn't extract rent from item ID {dataID} : {rentString.get_text()}"
                )
            else:
                logger.debug(
                    f"Extracted rent for item with ID {dataID,}. Item rent : {rent} CHF"
                )

        return rent if rent != None else 0
    
    def _formatRoomsStringHelper(self, dataID, roomsString):
        """
        getAds's helper function to extract and format rooms string.

        Params
        ------
        dataID : int
            Ad's data-id.
        roomsString : bs4.element.Tag
            Ad's raw rooms string.

        Returns
        -------
        rooms : float
            Ad's rooms.
        """
        rooms = None
        if roomsString != None:
            try:
                rooms = float(re.search(r"\d+\.?\d?", roomsString).group())
            except AttributeError:
                logger.warning(
                    f"Couldn't extract rooms from item ID {dataID} : {roomsString}"
                )
            else:
                logger.debug(
                    f"Extracted rooms for item with ID {dataID}. Item rooms : {rooms}"
                )
        else:
            logger.warning(f"Ad with ID {dataID} had no rooms indicated !")
        
        return rooms if rooms != None else 0
    
    def _formatSizeStringHelper(self, dataID, sizeString):
        """
        getAds's helper function to extract and format size string.

        Params
        ------
        dataID : int
            Ad's data-id.
        sizeString : bs4.element.Tag
            Ad's raw size string.

        Returns
        -------
        size : int
            Ad's size.
        """
        size = None
        if sizeString != None:
            try:
                size = int(re.search(r"\d+\.?\d?", sizeString.get_text()).group())
            except AttributeError:
                logger.warning(
                    f"Couldn't extract size from item ID {dataID} : {sizeString}"
                )
            else:
                logger.debug(
                    f"Extracted size for item with ID {dataID}. Item size : {size} m2"
                )
        else:
            logger.warning(f"Ad with ID {dataID} had no size indicated !")
        
        return size if size != None else 0
    
    def _getAdLinkHelper(self, dataID, adContainerSoup):
        """
        getAds's helper function to extract ad's link.

        Params
        ------
        dataID : int
            Ad's data-id.
        adContainerSoup : bs4.element.Tag
            Ad's container soup.

        Returns
        -------
        adURL : str
            Ad's URL.
        """
        adURL = None

        try:
            link = adContainerSoup.find(id=f"link-result-item-{dataID}")
        except KeyError:
            logger.warning(f"No link for item with data-id {dataID} : KeyError !")
            logger.debug(f"No link for item with data-id {dataID} : KeyError ! \nData dump : {adContainerSoup}")
        else:
            if link != None:
                adURL = self.URLs["website"] + link["href"]
                logger.debug(f"Extracted link for item with data-id {dataID} : {adURL}")
        
        return adURL

    def _getContactInfosHelper(self, dataID, adSoup):
        """
        getAds's helper function to extract ad's contact infos.

        Params
        ------
        dataID : int
            Ad's data-id.
        adSoup : bs4.element.Tag
            Ad's soup.

        Returns
        -------
        contactInfos : dict
            Ad's contact infos.
        """
        companyContactInfos = {}

        try:
            contactInfosSoup = FlatHunterBase.getElementsByClass(adSoup, get="first", _class="im__postDetails__contact")
        except KeyError:
            logger.warning(f"No company contact infos for item with data-id {dataID} : KeyError !")
            logger.debug(f"No company contact infos for item with data-id {dataID} : KeyError ! \nData dump : {adSoup}")
        else:
            if contactInfosSoup != None:
                addressBS4 = contactInfosSoup.find("address")
                if addressBS4 != None:
                    # Extract contact infos
                    contentList = addressBS4.contents
                    addressData = []
                    # Get company name
                    for el in contentList:
                        if el.name == "strong":
                            companyContactInfos["company-name"] = el.get_text().strip()
                            
                    # Get company address
                    for el in contentList:
                        if el.name == "strong":
                            pass
                        else:
                            stripElement = el.get_text().strip()
                            if stripElement != "":
                                addressData.append(stripElement)
                            
                    # Add company infos to contact infos dict
                    companyContactInfos["company-address"] = addressData         
            else:
                logger.warning(f"No company contact infos for item with data-id {dataID} : contactInfosSoup is None !")
        
        return companyContactInfos
    
    def _getChargesInTable(self, dataID, infoTableList):
        """
        getAds's helper function to extract charges from ad's table.

        Params
        ------
        dataID : int
            Ad's data-id.
        infoTableList : list
            Ad's table.

        Returns
        -------
        charges : int
            Ad's charges.
        """
        isChargesIndicated = False
        charges = 0
        for row in infoTableList:
            if "Charges :" in row:
                try:
                    charges = int(re.search(r"\d+", row).group())
                except:
                    logger.warning(f"Couldn't extract string charges in table from ad with ID {dataID} !")
                    logger.debug(f"Couldn't extract string charges in table from ad with ID {dataID} ! \nTable dump : {infoTableList}")
                else:
                    isChargesIndicated = True
                    logger.debug(f"Extracted charges from table for ad with ID {dataID}. Charges : {charges} CHF")
        
        if not isChargesIndicated:
            logger.warning(f"No charges were indicated in table for ad with ID {dataID}")
            return charges
        else:
            return charges
    
    def _getAddressHelper(self, dataID, adContentSoup):
        """
        getAds's helper function to extract address from ad.

        Params
        ------
        dataID : int
            Ad's data-id.
        adContentSoup : bs4.element.Tag
            Ad's content soup.

        Returns
        -------
        address : str
            Ad's address or empty string.
        """
        address = None
        try:
            # Last <p> tag contains address
            address = adContentSoup.find_all("p")[-1].get_text()
        except:
            logger.warning(f"Couldn't extract address from ad with ID {dataID} !")
            logger.debug(f"Couldn't extract address from ad with ID {dataID} ! \nDumping ad content : {adContentSoup}")
        else:
            logger.debug(f"Extracted address from ad with ID {dataID} : {address}")
        
        return address if address != None else ""

    def followAdLinkAndExtractData(self, dataID, adLink):
        """
        Function to follow ad link and extract ad's data.

        Params
        ------
        dataID : int
            Ad's data-id.
        adLink : str
            Ad's link.

        Returns
        -------
        adData : dict
            Ad's data or empty dict.
        """
        adData = {}
        if adLink != None:
            logger.debug(
                    f"Trying connection to item's page at URL : {adLink}"
                )
            # Get ad's page soup
            adPageSoup = self.getPageSoup(adLink)
            # == Get Contact informations == #
            adData["company-contact-infos"] = self._getContactInfosHelper(dataID, adPageSoup)
            # == Get images == #
            images = self._getImagesHelper(dataID, adPageSoup)
            adData["images"] = images
            # == Get ad's description == #
            descriptionBS4 = FlatHunterBase.getElementsByClass(adPageSoup, get="first", _class="im__postContent__body")
            adData["description"] = descriptionBS4.get_text() if descriptionBS4 != None else ""
            # == Get info table rows == #
            infoTableRowsBS4 = FlatHunterBase.getElementsByClass(adPageSoup, get="all", _class="im__table__row")
            if infoTableRowsBS4 != None:
                adData["infos"] = [info.get_text() for info in infoTableRowsBS4]
                # == Extract charges from table == #
                adData["charges"] = self._getChargesInTable(dataID, adData["infos"])
            else:
                logger.warning(f"No info table found in page for ad with ID {dataID} !")   
        else:
            logger.warning(
                f"Couldn't reach item's page, no link extracted for item with id {dataID}"
            )
        return adData