from FlatHunter.modules.ImmoCH import ImmoCH
import unittest
from bs4 import BeautifulSoup, Tag

class TestImmoCH(unittest.TestCase):
    """
    Test ImmoCH class.
    """
    def setUp(self):
        self.test_object = ImmoCH("flat")
        # Create test URL (with flats params)
        self.test_URL = self.test_object.URLs["flats"]["mainURL"] + self.test_object.URLs["flats"]["params"]
        self.test_soup = self.test_object.getPageSoup(self.test_URL)

    #@unittest.skip("Skip test_getItems()")
    def test_getItems(self):
        # Large search
        filterParams = {
            "minRent": 400,
            "maxRent": 5000,
            "minSize": 45,
            "maxSize": 350,
            "minRooms": 2.0,
            "maxRooms": 8.0,
        }
        filteredAds = self.test_object.getItems(filterParams, pagesToSearch=1)
        self.assertGreater(len(filteredAds), 5) # Is there at least 5 ads in returned list ?
        # Check if each ad is a dict with the right attributes and if values are of the right type.
        for ad in filteredAds:
            self.assertIn("data-id", ad) # Is there a data-id attribute ?
            self.assertIn("link", ad) # Is there a link attribute ?
            self.assertIn("images", ad) # Is there a images attribute ?
            self.assertIn("rent", ad) # Is there a rent attribute ?
            self.assertIn("rooms", ad) # Is there a rooms attribute ?
            self.assertIn("size", ad) # Is there a size attribute ?
            self.assertIsInstance(ad["data-id"], int) # Is data-id an int ?
            self.assertIsInstance(ad["link"], str) # Is link a string ?
            self.assertIsInstance(ad["images"], dict) # Is images a dict ?
            self.assertIsInstance(ad["rent"], int) # Is rent an int ?
            self.assertIsInstance(ad["rooms"], float) # Is rooms a float ?
            self.assertIsInstance(ad["size"], int) # Is size an int ?
        # Print first ad to check if it looks ok
        # print(filteredAds[0])
        print("\n Scraped " + str(len(filteredAds)) + " ads.\n")
    
    @unittest.skip("Skip test_getElementsByClass()")
    def test_getElementsByClass(self):
        """
        Test if getElementsByClass() returns a list of Tag objects.
        """
        testList = self.test_object.getElementsByClass(self.test_soup, get="all", _class="filter-item")
        testTag = self.test_object.getElementsByClass(self.test_soup, get="first", _class="filter-item")
        self.assertIsInstance(testList, list) # Is it a list ?
        self.assertIsInstance(testList[0], Tag) # Is it a list of Tag objects ?
        self.assertGreater(len(testList), 5) # Is there at least one element in list ?
        self.assertIsInstance(testTag, Tag) # Is it a Tag object ?

    @unittest.skip("Skip test_searchPages()")
    def test_searchPages(self):
        """
        Test if searchPages() returns a list and if it contains at least one page with 5 ads inside.
        """
        searchList = self.test_object.searchPages(pagesToSearch=1)
        self.assertIsInstance(searchList, list) # Is it a list of lists ?
        self.assertGreater(len(searchList), 0) # Is there at least one page ?
        self.assertGreater(len(searchList[0]), 5) # Is there at least 5 ads ?

    @unittest.skip("Skip test_getAds()")
    def test_getAds(self):
        """
        Check if it returns a list of at least 5 ads, if each ad is a dict with the right attributes 
        and if values are of the right type. 
        """
        adsList = self.test_object.getAds(self.test_soup)
        self.assertTrue(isinstance(adsList, list)) # Is it a list ?
        self.assertGreater(len(adsList), 5) # Is there at least 5 ads ?
        # Check if all attributes of first dict are present
        self.assertIn("data-id", adsList[0]) # Is there a data-id attribute ?
        self.assertIn("link", adsList[0]) # Is there a link attribute ?
        self.assertIn("ad-content-soup", adsList[0]) # Is there a ad-content-soup attribute ?
        self.assertIn("ad-character-soup", adsList[0]) # Is there a ad-character-soup attribute ?
        self.assertIn("ad-page-soup", adsList[0]) # Is there a ad-page-soup attribute ?
        # Check if values of first dict are of the right type
        self.assertIsInstance(adsList[0]["data-id"], int) # Is data-id an int ?
        self.assertIsInstance(adsList[0]["link"], str) # Is link a string ?
        self.assertIsInstance(adsList[0]["ad-content-soup"], Tag) # Is ad-content-soup a BeautifulSoup Tag object ?
        self.assertIsInstance(adsList[0]["ad-character-soup"], Tag) # Is ad-character-soup a BeautifulSoup Tag object ?
        self.assertIsInstance(adsList[0]["ad-page-soup"], Tag) # Is ad-page-soup a BeautifulSoup Tag object ?

    @unittest.skip("Skip test_getNumberOfPages()")
    def test_getNumberOfPages(self):
        """
        Test if getNumberOfPages() returns an integer.
        """
        nbOfPages = self.test_object.getNumberOfPages(self.test_soup)
        self.assertIsInstance(nbOfPages, int) # Is it an integer ?

if __name__ == "__main__":
    unittest.main()