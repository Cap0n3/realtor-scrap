from FlatHunter.modules.ImmoCH import ImmoCH
import json 

FILTER = {
    "minRent": 400,
    "maxRent": 5000,
    "minSize": 45,
    "maxSize": 350,
    "minRooms": 2.0,
    "maxRooms": 8.0,
}

obj = ImmoCH("flat")
items = obj.getItems(FILTER, pagesToSearch=1)

for dic in items:
    print(json.dumps(dic, indent=4))
    print("\n\n")