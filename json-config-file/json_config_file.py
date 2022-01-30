import os
import json
from json import JSONEncoder

config_file_name = "config.json"

class Point:
    def __init__(self, x: int, y: int):
        self.X = x
        self.Y = y

class Rectangle:
    def __init__(self, point: Point):
        self.Point1st = point
        self.Point2nd = None

class Level:
    def __init__(self, min: int):
        self.Min = min
        self.Max = None

class Picking:
    def __init__(self, id: str):
        self.Id = id
    def Set1stPoint(self, x: int, y: int):
        self.Area = Rectangle(Point(x, y))
    def Set2ndPoint(self, x: int, y: int):
        self.Area.Point2nd = Point(x, y)
    def SetMinDepth(self, min: int):
        self.Depth = Level(min)
    def SetMaxDepth(self, max: int):
        self.Depth.Max = max

def picking_from_json(json: dict):
    picking = Picking(json["Id"])
    picking.Area = area_from_json(json["Area"])
    picking.Depth = depth_from_json(json["Depth"])
    return picking

def area_from_json(json: dict):
    area = Rectangle(point_from_json(json["Point1st"]))
    area.Point2nd = point_from_json(json["Point2nd"])
    return area

def point_from_json(json: dict):
    point = Point(json["X"], json["Y"])
    return point

def depth_from_json(json: dict):
    depth = Level(json["Min"])
    depth.Max = json["Max"]
    return depth

class CustomEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

if os.path.isfile(config_file_name):
    with open(config_file_name, "r") as json_file:
        config_data = json.load(json_file)
        print("Read successful")
        json_file.close()
else:
    config_data = {}
    default_json = json.dumps(config_data)
    with open(config_file_name, "w") as json_file:
        json_file.write(default_json)
        print("Config file created")
        json_file.close()

keys = config_data.keys()

for key in keys:
    config_data[key] = picking_from_json(config_data[key])

choices = ["CREATE", "UPDATE", "DELETE", "PRINT", "SAVE", "EXIT"]
choice_text = "Please choose an option:\n"
for index, choice in enumerate(choices):
    choice_text += f"\t{str(index)} {choice}\n"

options = ["Id", "Area 1st Point", "Area 2nd Point", "Min Depth", "Max Depth"]
option_text = "Please select a property to update:\n"
for index, option in enumerate(options):
    option_text += f"\t{str(index)} {option}\n"

continuing = True

while continuing:
    choice = input(choice_text)
    choice = int(choice)
    if choice == 0:
        id = input("Please enter Part Code:\n")
        config_data[id] = Picking(id)

        x1 = input("Please enter 1st Point X:\n")
        y1 = input("Please enter 1st Point Y:\n")
        config_data[id].Set1stPoint(int(x1), int(y1))

        x2 = input("Please enter 2nd Point X:\n")
        y2 = input("Please enter 2nd Point Y:\n")
        config_data[id].Set2ndPoint(int(x2), int(y2))

        min = input("Please enter Min Depth:\n")
        config_data[id].SetMinDepth(int(min))

        max = input("Please enter Max Depth:\n")
        config_data[id].SetMaxDepth(int(max))
    elif choice == 1:
        update_text = "Please select an item to update:\n"
        for key in keys:
            update_text += f"\t{key}\n"
        update = input(update_text)
        if update in keys:
            property = input(option_text)
            property = int(property)
            if property == 0:
                update_id = input("Please enter new Part Code:\n")
                config_data[update].Id = update_id
                config_data[update_id] = config_data.pop(update)
            elif property == 1:
                update_x1 = input("Please enter new 1st Point X:\n")
                update_y1 = input("Please enter new 1st Point Y:\n")
                config_data[update].Area.Point1st = Point(int(update_x1), int(update_y1))
            elif property == 2:
                update_x2 = input("Please enter new 2nd Point X:\n")
                update_y2 = input("Please enter new 2nd Point Y:\n")
                config_data[update].Area.Point2nd = Point(int(update_x2), int(update_y2))
            elif property == 3:
                update_min = input("Please enter new Min Depth:\n")
                config_data[update].Depth.Min = update_min
            elif property == 4:
                update_max = input("Please enter new Max Depth:\n")
                config_data[update].Depth.Max = update_max
            else:
                print(f"Property '{property}' not found")
        else:
            print(f"Item '{update}' not found")
    elif choice == 2:
        delete_text = "Please select an item to delete:\n"
        for key in keys:
            delete_text += f"\t{key}\n"
        delete = input(delete_text)
        if delete in keys:
            del config_data[delete]
        else:
            print(f"Item '{delete}' not found")
    elif choice == 3:
        json_data = json.dumps(config_data, indent=4, cls=CustomEncoder)
        print(json_data)
    elif choice == 4:
        with open(config_file_name, "w") as json_file:
            json.dump(config_data, json_file, cls=CustomEncoder, indent=4)
            print("Write successful")
            json_file.close()
    elif choice == 5:
        break
    else:
        cont = input("Do you want to try again? Yes/No\n")

        if cont in ["y", "Y", "yes", "Yes", "YES"]:
            continuing = True
        elif cont in ["n", "N", "no", "No", "NO"]:
            continuing = False