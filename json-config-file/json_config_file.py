import os
import json

config_file_name = "config.json"

if os.path.isfile(config_file_name):
    with open(config_file_name, "r") as json_file:
        config_data = json.load(json_file)
        print("Read successful")
        json_file.close()
else:
    config_data = {
        "domain" : "sergio",
        "language" : "python",
        "date" : "20/12/2021",
        "topic" : "config file"
    }
    default_json = json.dumps(config_data)
    print(default_json)
    with open(config_file_name, "w") as json_file:
        json_file.write(default_json)
        print("Write successful")
        json_file.close()

print(config_data)
config_data['date'] = '30/01/2022'
print("Date updated from 20/12/2021 to 30/01/2022")

with open(config_file_name, "w") as json_file:
    updated_json = json.dump(config_data, json_file)
    print(config_data)
    print("Update successful")
    json_file.close()

print(config_data)