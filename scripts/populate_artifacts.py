#!/usr/bin/env python
import argparse
import csv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--artifacts-file",
                        type=argparse.FileType('r', encoding='utf-8'),
                        help="Path to the config file with features to use",
                        required=True)
    parser.add_argument("-u", "--update",
                        action="store_true",
                        default=False,
                        required=False,
                        help="Update if the name exists.")
    args = parser.parse_args()


    artifacts_info = csv.reader(args.artifacts_file)

    client = MongoClient()
    client = MongoClient("localhost", 27017)
    db = client.testdb

    for i, row in enumerate(artifacts_info):
        if i == 0:
            continue
        type_ = row[0]
        name = row[1]
        latitude = float(row[2])
        longitude = float(row[3])

        data = {
            "type": type_,
            "name": name,
            "latitude": latitude,
            "longitude": longitude
        }
        try:
            id_ = db.artifacts.insert_one(data.copy())
            print(id_)
        except DuplicateKeyError:
            print("Cannot insert data for {}, because it exists.".format(name))
            if args.update:
                print("Update data for artifact with name {}".format(name))
                del data["name"]

                print(data)
                res = db.artifacts.update_one({"name": name, "type": type_}, {"$set": data})
                print("res: ", res.raw_result)
