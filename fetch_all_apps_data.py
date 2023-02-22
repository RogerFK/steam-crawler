"""
This script crawls game data for every game in an input file.
Author: Jorge González
Date: 2023-02-10
"""

from steam import Steam
from decouple import config, UndefinedValueError
from requests import request, Response
import json
import time
import steamreviews
import logging

# we only need to log basic characters, no localized names, this saves some space
logging.basicConfig(filename='example.log', encoding='ascii', level=logging.DEBUG)

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

import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
)
cursor = mydb.cursor(prepared=True)
stmt = "INSERT INTO steam_games (appid, name, developer, publisher, score_rank, positive, negative, userscore, owners, average_forever, average_2weeks, median_forever, median_2weeks, price,"
stmt += "initialprice, discount, ccu, genres, tags, languages, achievements, release_date, last_update, required_age, dlc, detailed_description, about_the_game, short_description, supported_languages, header_image, website, pc_requirements, mac_requirements, linux_requirements, legal_notice, developers, publishers, price_overview, packages, package_groups, platforms, categories, genres, screenshots, movies, recommendations, achievements, release_date, support_info, background, content_descriptors) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
stmt = stmt.replace("?,", "%s,").replace("?)", "%s)")

def get_app_data(file):
    with open(file, "r", encoding="utf-8") as f:
        for line in f:
            app_id = line.strip()
            retry = True
            consecutive_retries = 0
            while retry:
                try:
                    response = request("get", "https://store.steampowered.com/api/appdetails", params={"appids": app_id})
                except Exception as e:
                    print("Exception while requesting appdetails: " + str(e))
                    time.sleep(60 + consecutive_retries * 30)
                    consecutive_retries += 1
                    if consecutive_retries > 18: # maximum waiting time for the connection to be back: 10 minutes
                        # this high number also ensures the user can fix the problem without having to restart the script
                        consecutive_retries = 18
                    continue
                retry = response.status_code != 200
                if retry:
                    print(f"REST API error ({response.status_code}): " + str(response.text))
                    print("Headers: " + str(response.headers))
                    print("Request headers: " + str(response.request.headers))
                    time.sleep(60 + consecutive_retries * 30)
                    consecutive_retries += 1
                    if consecutive_retries > 6: # maximum waiting time: 4 minutes (which might be too much, but better safe than sorry)
                        consecutive_retries = 6
            appdata = json.loads(response.text)
            if appdata[app_id]["success"]:
                # First, check if this is a game
                if "type" in appdata[app_id]["data"] and appdata[app_id]["data"]["type"] != "game":
                    logging.debug("Skipping non-game: " + appdata[app_id]["data"]["name"])
                    continue
                request_params = dict()
                # Reference: https://partner.steamgames.com/doc/store/getreviews
                request_params['review_type'] = 'positive'
                request_params['filter'] = 'updated'
                # note: it would be interesting to use the "last update" date of the game, but
                # https://partner.steam-api.com/ISteamApps/GetAppDepotVersions/v1/ doesn't work for games I don't own an access token for 
                request_params['day_range'] = '28' # day_range = 28 is last two weeks, usually enough to paint a picture of the game's current state  
                request_params['purchase_type'] = 'all'
                request_params['num_per_page'] = '100'
                request_params['cursor'] = '*'
                request_params['language'] = 'all'

                review_dict, query_count = steamreviews.download_reviews_for_app_id(int(app_id),
                                                                                chosen_request_params=request_params)
                print("Review Dict", review_dict)
                print("Query count", query_count)
                # TODO change to MYSQL insert
                with open("data/" + app_id + ".json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(appdata[app_id]["data"]))
                print("App ID: " + app_id + " done.")
                # debug
                input("Press Enter to continue...")
            else:
                print(f"Error for app ID {app_id}: " + response.text)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl game data for every game in an input file.")
    parser.add_argument("file", help="The name of the file.")
    args = parser.parse_args()
    get_app_data(args.file)