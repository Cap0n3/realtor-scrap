import unittest
import os
from bs4 import BeautifulSoup, Tag
from FlatHunter.utils.abstract_base import FlatHunterBase
from FlatHunter.utils.misc_utils import getPath

ROOT_PATH = getPath("root")

# Get local page soup for testing purposes
AD_PAGE_PATH = f"{ROOT_PATH}/FlatHunter/tests/LocalQueryTests/PagesToQuery/immo_searchPage.html"
with open(AD_PAGE_PATH) as fp:
    LOCAL_PAGE_SOUP = BeautifulSoup(fp, 'html.parser')

class FlatHunterBaseChild(FlatHunterBase):
    """
    Child class of FlatHunterBase abstract class. Used for testing purposes.
    """
    def getAds(self):
        print("Hello getAds!")
    def getItems(self):
        print("Hello getItems!")
    def getNumberOfPages(self):
        print("Hello getNumberOfPages!")
    def searchPages(self):
        print("Hello searchPages!")

class TestFlatHunterBase(unittest.TestCase):
    """
    Test static methods of FlatHunterBase abstract class.
    """
    def setUp(self):
        self.test_dict = {"test": "test"}
        self.filename = "test.search"
        self.test_object = FlatHunterBaseChild("flat")
        self.test_object.saveObject(self.test_dict, self.filename, test=True)
        self.test_object.loadObject(self.filename)

    def test_getElementsByClass(self):
        """
        Test getElementsByClass method with local page soup.
        """
        testList = self.test_object.getElementsByClass(LOCAL_PAGE_SOUP, get="all", _class="filter-item")
        testTag = self.test_object.getElementsByClass(LOCAL_PAGE_SOUP, get="first", _class="filter-item")
        self.assertIsInstance(testList, list) # Is it a list ?
        self.assertIsInstance(testList[0], Tag) # Is it a list of Tag objects ?
        self.assertGreater(len(testList), 5) # Is there at least one element in list ?
        self.assertIsInstance(testTag, Tag) # Is it a Tag object ?
    
    def test_saveObject(self):
        self.assertEqual(self.test_dict, self.test_object.loadObject(self.filename)["object"])
    
    def test_loadObject(self):
        self.assertEqual(self.test_dict, self.test_object.loadObject(self.filename)["object"])
    
    def tearDown(self):
        os.remove(f"{ROOT_PATH}/data/output/{self.filename}")

if __name__ == "__main__":
    unittest.main()
