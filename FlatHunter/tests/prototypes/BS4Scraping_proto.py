from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
import re
from FlatHunter.utils.logging_utils import logger
import pickle
from datetime import datetime
#import pandas as pd

#self.baseURL = "https://www.immobilier.ch"
#url = "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/page-1?t=rent&c=1;2&p=s40&nb=false&gr=1"

# =================================== #
# ========= UTILS FUNCTIONS ========= #
# =================================== #

def saveObject(obj, site):
    """
    Save object to a file for later analyse.
    """
    filename = f"savedObjects/{datetime.now()}_{site}.pickle"
    try:
        with open(filename, "wb") as f:
            pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print("Error during unpickling object (Possibly unsupported):", e)

def loadObject(filename):
    """
    Load pickle object.
    """
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except Exception as ex:
        print("Error during unpickling object (Possibly unsupported):", ex)

# =========================== #
# ========= CLASSES ========= #
# = ========================== #

class ImmoFlats:
    def __init__(self, totalPages=None):
        self.firstPageURL = "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve/page-1?t=rent&c=1;2&p=s40&nb=false&gr=1"
        self.baseURL = "https://www.immobilier.ch/fr/carte/louer/appartement-maison/geneve"
        self.urlParams = "?t=rent&c=1;2&p=s40&nb=false&gr=1"
        self.siteURL = "https://www.immobilier.ch"

        # ====================== #
        # === CORE FUNCTIONS === #
        # ====================== #
        def handleResponse(_url):
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
                return response

        def getNbOfPages(_soup):
            """
            Find total number of pages in immobilier.ch search.

            Return
            ------
            lastPageNumber : int
                Number representing last pages of search.
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

        def getFlatInfos(_itemsList):
            """
            Extract item informations on page & item details on item's page.

            Returns
            -------
            list : allFlatList
                List containing all extracted information in page (flat dictionnaries)
            """
            allFlatList = []
            for item in _itemsList:
                flatDict = {}
                # === Extract data-id of item === #
                try:
                    dataID = item['data-id']
                except KeyError:
                    flatDict["data-id"] = "-"
                    logger.warn("No data-id for item : KeyError")
                else:
                    flatDict["data-id"] = dataID
                # === Extract link of item === #
                try:
                    link = item.find(id=f"link-result-item-{dataID}")
                except KeyError:
                    flatDict["link"] = "-"
                    logger.warn(f"No link for item with data-id {flatDict['data-id']} : KeyError")
                else:
                    if link != None:
                        flatDict["link"] = self.siteURL + link["href"]
                # === Extract rooms === #
                try:
                    rawRooms = item.find(class_="object-type")
                except KeyError:
                    flatDict["rooms"] = "-"
                    logger.warn(f"No rooms indicated for item with data-id {flatDict['data-id']} : KeyError")
                else:
                    if rawRooms != None:
                        try:
                            rooms= re.search(r"\d+\.?\d?", rawRooms.get_text()).group()
                        except AttributeError:
                            flatDict["rooms"] = "-"
                            logger.error(f"Couldn't extract rooms for item with data-id {flatDict['data-id']} : AttributeError")
                        else:
                            flatDict["rooms"] = float(rooms)
                # === Extract rent, charges, size & address (same bloc) === #
                try:
                    contentDiv = item.find(class_="filter-item-content")
                except KeyError:
                    flatDict["rent"] = "-"
                    flatDict["charges"] = "-"
                    flatDict["address"] = "-"
                    logger.warn(f"Couldn't extract <div> with class 'filter-item-content' for item with data-id {flatDict['data-id']} : KeyError")
                else:
                    if contentDiv != None:
                        # << Get rent & charges >> #
                        # Remove thousand separator
                        rawRent = re.sub("'", "", contentDiv.find(class_="title").get_text())
                        rentStr = re.search(r"CHF\s\d+\.-/mois", rawRent)
                        chargesStr = re.search(r"\+\s\d+\.-", rawRent)
                        if rentStr != None:
                            rent = re.search(r"\d+", rentStr.group()).group()
                            flatDict["rent"] = rent
                        if chargesStr != None:
                            charges = re.search(r"\d+", chargesStr.group()).group()
                            flatDict["charges"] = charges
                        # << Get address >> #
                        allparagraphs = contentDiv.find_all("p")
                        # Get last <p> where address is
                        address = allparagraphs[-1].get_text()
                        flatDict["address"] = address
                        
                # === Extract flat surface === #
                try:
                    characterDiv = item.find(class_="filter-item-characteristic")
                except AttributeError:
                    logger.warn(f"Couldn't extract <div> with class 'filter-item-characteristic' for item with data-id {flatDict['data-id']} : AttributeError")
                else:
                    if characterDiv != None:
                        try:
                            rawSpace = characterDiv.find(class_="space").get_text()
                        except AttributeError:
                            logger.warn(f"No flat surface indicated in <div> class 'filter-item-characteristic' for item with data-id {flatDict['data-id']} : AttributeError")
                        else:
                            space = re.search(r"\d+", rawSpace).group()
                            flatDict["space"] = space
                # === Go to item's page & scrap more details (description, images) === #
                if "link" in flatDict:
                    resp = handleResponse(flatDict["link"])
                    soup = BeautifulSoup(resp.content, "html.parser")
                    # << Get description >> #
                    try:
                        descriptionDiv = soup.find(class_="im__postContent__body")
                    except Exception as e:
                        flatDict["description"] = "-"
                        logger.warn(f"An error occured with item description, couldn't find <div> with class 'im__postContent__body' for item with data-id {flatDict['data-id']} : {e}")
                    else:
                        try:
                            textParagraphs = descriptionDiv.find_all("p")
                        except AttributeError:
                            logger.warn(f"Coudln't find <p> in description for item with data-id {flatDict['data-id']} : AttributeError\n{soup}")
                            flatDict["description"] = "-"
                        else:
                            descriptionString = ""
                            # Format a bit text
                            for p in textParagraphs:
                                text = p.get_text() + "\n"
                                descriptionString += text
                            flatDict["description"] = descriptionString
                    # << Get item's image links >> #
                    allImagesTags = soup.find_all(class_="img-responsive")
                    # Store image's links in set to avoid duplicates
                    imageLinksSet = set()
                    for imageTag in allImagesTags:
                        try:
                            imageLink = imageTag["data-lazy"]
                        except KeyError:
                            logger.warn(f"No attribute named 'data-lazy' in image tag for item with data-id {flatDict['data-id']} (KeyError) IMAGE TAG : {imageTag}")
                        else:
                            imageLinksSet.add(imageLink)
                    flatDict["item-image-links"] = imageLinksSet
                    flatDict["source"] = "immobilier.ch"
                # === Append dict in list === #
                logger.debug(flatDict)
                allFlatList.append(flatDict)
            return allFlatList

        # ============ #
        # === MAIN === #
        # ============ #

        # === Get total number of pages === #
        resp = handleResponse(self.firstPageURL)
        soup = BeautifulSoup(resp.content, "html.parser")
        self.totalPages = totalPages
        # If number of pages is not specified, get them all
        if self.totalPages == None:
            self.totalPages = getNbOfPages(soup)
        logger.info(f"Pages to be scraped = {self.totalPages} pages")

        # === Scrap all pages === #
        allFlats = []
        for pageNb in range(1, self.totalPages + 1):
            # Construct complete url for each pages
            url = f"{self.baseURL}/{pageNb}{self.urlParams}"
            resp = handleResponse(url)
            soup = BeautifulSoup(resp.content, "html.parser")
            itemsList = soup.find_all(class_="filter-item")
            flatList = getFlatInfos(itemsList)
            allFlats += flatList
        # Create main attribute
        self.allFlats = allFlats

    def getFlats(self):
        return self.allFlats

    def getPrettyFlat(self):
        htmlHead = """
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <title>Hello, world!</title>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width,initial-scale=1" />
                <meta name="description" content="" />
            </head>
            <body> 
        """
        htmlBottom = """
            </body>
        </html>
        """
        with open("FlatPage.html", "w") as f:
            f.writelines(htmlHead)
            for flat in self.allFlats:
                f.writelines("<table>")
                f.writelines("<tr>")
                f.writelines("<th scope='col'>Address</th>")
                f.writelines("</tr>")
                f.writelines("<tr>")
                f.writelines(f"<td>{flat['address']}</td>")
                f.writelines("</tr>")
                f.writelines("</table>")


# ====== SEARCH ====== #
obj = ImmoFlats(totalPages=1)
# Save object in file
saveObject(obj, "immoCH")

# savedObj = loadObject("savedObjects/2022-11-08 00:37:38.807381_immoCH.pickle")

# rows = []
# for data in savedObj.getFlats():
#     id = data["data-id"]
#     try:
#         data["address"]
#     except:
#         address = "-"
#     else:
#         address = data["address"]

# df = pd.DataFrame(rows)