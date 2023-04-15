import unittest
import os
from FlatHunter.utils.abstract_base import FlatHunterBase
from FlatHunter.utils.misc_utils import getPath

ROOT_PATH = getPath("root")

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
    
    def test_saveObject(self):
        self.assertEqual(self.test_dict, self.test_object.loadObject(self.filename)["object"])
    
    def test_loadObject(self):
        self.assertEqual(self.test_dict, self.test_object.loadObject(self.filename)["object"])
    
    def tearDown(self):
        os.remove(f"{ROOT_PATH}/data/output/{self.filename}")

if __name__ == "__main__":
    unittest.main()
