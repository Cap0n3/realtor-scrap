from FlatHunter.modules.ImmoCH import ImmoCH
import unittest

# Design me a test for this class
class TestImmoCH(unittest.TestCase):
    def setUp(self):
        self.test_object = ImmoCH("flat")
        # Create test URL (with flats params)
        self.test_URL = self.test_object.URLs["flats"]["mainURL"] + self.test_object.URLs["flats"]["params"]
        self.test_soup = self.test_object.getPageSoup(self.test_URL)

    def test_getAds(self):
        """
        Check if it returns a list of at least 5 ads, if each ad is a dict with the right attributes 
        and if values are of the right type. 
        """
        adsList = self.test_object.getAds(self.test_soup)
        self.assertTrue(isinstance(adsList, list)) # Is it a list ?
        self.assertGreater(len(adsList), 5) # Is there at least 5 ads ?
        print(type(adsList[0]['ad-content-soup']))
        # Check if all attributes of first dict are present
        self.assertIn("data-id", adsList[0]) # Is there a data-id attribute ?
        self.assertIn("link", adsList[0]) # Is there a link attribute ?
        self.assertIn("ad-content-soup", adsList[0]) # Is there a ad-content-soup attribute ?
        self.assertIn("ad-character-soup", adsList[0]) # Is there a ad-character-soup attribute ?
        self.assertIn("item-page-soup", adsList[0]) # Is there a item-page-soup attribute ?
        # Check if values of first dict are of the right type
        self.assertIsInstance(adsList[0]["data-id"], int) # Is data-id an int ?
        self.assertIsInstance(adsList[0]["link"], str) # Is link a string ?
        self.assertIsInstance(adsList[0]["ad-content-soup"], object) # Is ad-content-soup an object ?
        self.assertIsInstance(adsList[0]["ad-character-soup"], object) # Is ad-character-soup an object ?
        self.assertIsInstance(adsList[0]["item-page-soup"], object) # Is item-page-soup an object ?

    def test_getItems(self):
        pass

    def test_getNumberOfPages(self):
        """
        Test if getNumberOfPages() returns an integer.
        """
        nbOfPages = self.test_object.getNumberOfPages(self.test_soup)
        self.assertIsInstance(nbOfPages, int) # Is it an integer ?

    def test_searchPages(self):
        """
        Test if searchPages() returns a list and if it contains at least one page with 5 ads inside.
        """
        searchList = self.test_object.searchPages(searchPages=1)
        self.assertIsInstance(searchList, list) # Is it a list of lists ?
        self.assertGreater(len(searchList), 0) # Is there at least one page ?
        self.assertGreater(len(searchList[0]), 5) # Is there at least 5 ads ?

    def tearDown(self):
        pass


if __name__ == "__main__":
    unittest.main()