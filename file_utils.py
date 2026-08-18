import csv
import json
import os


def read_csv(filepath): #read the csv data and return them as dictionary or list
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"file is not exist: {filepath}")

    with open(filepath, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]

    return data


def write_csv(filepath, data, fieldnames=None): #write the csv data to a file
    if not data:
        raise ValueError("empty data, nothing to write")

    if fieldnames is None:
        fieldnames = data[0].keys()

    with open(filepath, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def read_json(filepath): #read the json data and return them as dictionary or list
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"file is not exist: {filepath}")

    with open(filepath, mode="r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def write_json(filepath, data): #write the json data to a file
    with open(filepath, mode="w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)