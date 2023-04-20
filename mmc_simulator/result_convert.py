import os
import json
from experiment import *

def convert():
    dirPath = "../results/04-20-11-40-22"
    newDirPath = "../results/04-20-11-40-22-NEW"
    os.mkdir(newDirPath)
    for filename in os.listdir(dirPath):
        with open(os.path.join(dirPath, filename), 'r') as file:
            data = json.load(file)
        dataPath = os.path.join(newDirPath, os.path.splitext(filename)[0])
        os.mkdir(dataPath)
        for planData in data["planData"]:
            writeData(os.path.join(dataPath, f"seed-{planData['seed']}.json"), planData)
        del data["planData"]
        writeData(dataPath + ".json", data)

if __name__ == "__main__":
    convert()