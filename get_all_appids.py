"""
This script crawls game data for a single game.
Author: Jorge González
Date: 2023-02-10
"""

from steam import Steam
from decouple import config, UndefinedValueError
from requests import request, Response
import json

try:
    KEY = config("STEAM_API_KEY")
except UnicodeDecodeError as e:
    print("Ensure your .env/settings.ini file is encoded in UTF-8.")
    exit(-1)
except UndefinedValueError as e:
    print(e)
    print("Tips:\r\n- You can create an .env file with 'STEAM_API_KEY=\"YOUR_API_KEY\"'.")
    print("- You can also define an environment variable STEAM_API_KEY with your API key.")
    exit(-1)

steam = Steam(KEY)

def get_all_appids():
    response = request("get", "https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    print("Response code: " + str(response.status_code))
    if response.status_code == 200:
        # dump raw data, useful to manually check which game is which visually
        with open("appids_raw.json", "w", encoding="utf-8") as f:
            f.write(response.text)
        # dump appids
        with open("appids.txt", "w", encoding="utf-8") as f:
            for appdata in response.json()["applist"]["apps"]:
                f.write(str(appdata["appid"]) + "\n")
    else:
        print("Error: " + str(response.text))

if __name__ == "__main__":
    get_all_appids()
