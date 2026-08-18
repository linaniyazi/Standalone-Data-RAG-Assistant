from file_utils import read_csv, write_csv, read_json, write_json

#read csv
data = read_csv("data/sample.csv")
print(data)

#write json from the same data 
write_json("data/sample.json", data)

#read json
json_data = read_json("data/sample.json")
print(json_data)

#make a copy of the csv and write in it
write_csv("data/sample_copy.csv", data)