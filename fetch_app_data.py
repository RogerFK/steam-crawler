"""
This script crawls game data for a single game.
Author: Jorge González
Date: 2023-02-10
"""

from steam import Steam
from decouple import config, UndefinedValueError
from requests import request, Response
import json
import steamreviews

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

def get_app_data(app_id):
    # Get app details
    response = steam.apps.get_app_details(app_id)
    with open(f"app_{app_id}_details.json", "w") as f:
        f.write(response)

    #steamreviews.download_reviews_for_app_id(int(app_id),
    #                                chosen_request_params={"cursor": 'AoJ49Yzl34EDf5SzwgM='}, verbose=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl game data for a single game.")
    parser.add_argument("appid", help="App ID of the game to fetch data for.")
    args = parser.parse_args()
    get_app_data(args.appid)
