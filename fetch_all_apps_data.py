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
from database import *
import os

main_script = False
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
# Used for steamreviews
# Reference: https://partner.steamgames.com/doc/store/getreviews
# note: it would be interesting to use the "last update" date of the game, but
# https://partner.steam-api.com/ISteamApps/GetAppDepotVersions/v1/ doesn't work for games I don't own an access token for 
request_params = {
    'review_type': 'all',
    'filter': 'updated',
    'day_range': '365',
    'num_per_page': '100',
    'language': 'all'
}

# monkey patching to stop steamreviews from trying to open the reviews file or saving to them
def get_output_filename(app_id):
    return "NUL:" if os.name == "nt" else "/dev/null"
steamreviews.download_reviews.get_output_filename = get_output_filename

def load_review_dict(app_id):
    # skips the file opening and loading
    review_dict = dict()
    review_dict["reviews"] = dict()
    review_dict["query_summary"] = steamreviews.download_reviews.get_dummy_query_summary()
    review_dict["cursors"] = dict()

    return review_dict
steamreviews.download_reviews.load_review_dict = load_review_dict

# These steam API rate limits still give headroom for the steamreviews library and my own calls to work
# rate limits per day are 100.000 queries, so 250 queries every 5 minutes should be fine, 
# specially if we have headroom for ~347 queries per 5 minutes (69.4 queries per minute)
# either way, to be more precise we can just do it per minute, and add 10 seconds of headroom
def get_steam_api_rate_limits():
    rate_limits = {
        "max_num_queries": 55,
        "cooldown": (60) + 10,  # 1 minute + 10 seconds of headroom
        "cooldown_bad_gateway": 10,  # arbitrary value to tackle 502 Bad Gateway due to saturated servers (during sales)
    }

    return rate_limits
steamreviews.download_reviews.get_steam_api_rate_limits = get_steam_api_rate_limits

def get_app_data(app_id, reviews=False):
    rate_limits = get_steam_api_rate_limits()
    retry = True
    consecutive_retries = 0
    if (is_processed(app_id)):
        print(f"App {app_id} already processed.")
        return
    while retry:
        try:
            # response = steam.apps.get_app_details(int(app_id)) # I need the response code... can't use this one
            response = request("GET", "https://store.steampowered.com/api/appdetails", params={"appids": app_id, "cc": "us", "l": "english"})
        except Exception as e:
            print("Exception while requesting appdetails: " + str(e))
            consecutive_retries += 1
            if consecutive_retries > 3 * 5: # maximum waiting time for the connection to be back: 5 minutes
                # this high number also ensures the user may fix the problem without having to restart the script
                consecutive_retries = 3 * 5
            
            print(f"Waiting {(consecutive_retries * 20 / 60)} minute(s) before retrying...")
            time.sleep(consecutive_retries * 20)
            continue
        
        retry = response.status_code != 200
        if retry:
            print(f"REST API error ({response.status_code}): " + str(response.text))
            print("Headers: " + str(response.headers))
            time.sleep(60 + consecutive_retries * 20)
            consecutive_retries += 1
            if consecutive_retries > 3: # maximum waiting time for the API to respond again: 2 minutes
                # this high number also ensures the user may fix the problem without having to restart the script
                consecutive_retries = 6
    
    appdata = json.loads(response.text)
    if appdata[app_id]["success"]:
        # First, check if this is a game
        if "type" in appdata[app_id]["data"] and appdata[app_id]["data"]["type"] != "game":
            print("Skipping non-game: " + appdata[app_id]["data"]["name"])
            return
        # Then, check if this game has reviews
        if reviews:
            print("Getting reviews for " + appdata[app_id]["data"]["name"])
            request_params['cursor'] = '*'
            review_dict, query_count = steamreviews.download_reviews_for_app_id(int(app_id),
                                                                            chosen_request_params=request_params, verbose=True)
            query_summary = review_dict["query_summary"]
        else:
            print("Skipping reviews for " + appdata[app_id]["data"]["name"])
            success_flag, query_summary, query_count = steamreviews.download_reviews.download_the_full_query_summary(app_id, 0, request_params)
        
        process_game_data(app_id, appdata[app_id]["data"], query_summary)

        process_game_reviews(app_id, review_dict["reviews"])
        
        mark_as_processed(app_id)

        print("App ID: " + app_id + " done.")
    else:
        print(f"Error for app ID {app_id}: " + response.text)

if __name__ == "__main__":
    main_script = True

    import argparse
    parser = argparse.ArgumentParser(description="Crawl game data for every game in an input file.")
    parser.add_argument("file", help="The name of the file.")
    args = parser.parse_args()
    
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                app_id = line.strip()
                get_app_data(app_id, reviews=True)
        # When we're done, delete the files and start getting appids from the database
        with open(args.file, "w", encoding="utf-8") as f:
            f.write("")
        
        # Get appids from the database
        raise KeyboardInterrupt
        while True: # wait for KeyboardInterrupt or no appids left, which will break the loop
            appids = cur.fetchone()
            if appids is None:
                break
            get_app_data(appids[0], reviews=True)
            con.commit()

    except KeyboardInterrupt:
        print("Exiting...")
        exit(0)
        # but first delete processed_appids from args.file
        with open(args.file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        cur.execute("SELECT appid FROM processed_appids")
        processed_appids = set(cur.fetchall())
        with open(args.file, "w", encoding="utf-8") as f:
            for line in lines:
                if line.strip() not in processed_appids:
                    f.write(line)
        # also save the last cursor from steamreviews