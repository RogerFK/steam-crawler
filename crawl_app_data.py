"""
This script crawls game data for every game in an input file.
Author: Jorge González
Date: 2023-02-10
"""

from typing import Tuple
from requests import request, Response

import json
import time
import steamreviews
from database import *
import os
from config import get_steam_api_rate_limits, check_rate_limit, request_params


# monkey patching to stop steamreviews from trying to open the reviews file or saving to them
# just to save on IO operations
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
steamreviews.download_reviews.get_steam_api_rate_limits = get_steam_api_rate_limits

SKIPPED = 4
FAULTY = 3
FULLY_PROCESSED = 2
ALREADY_EXISTS = 1
SUCCESS = 0
ERROR = -1

def get_app_data(app_id: str, reviews=False, query_count=0, only_games=True, verbose=True) -> Tuple[int, int]:
    retry = True
    consecutive_retries = 0
    game_data = get_game_data(app_id)
    exists = game_data is not None
    if (is_processed(app_id)):
        print(f"App {app_id} already processed.")
        return FULLY_PROCESSED, query_count
    elif (reviews == False and exists):
        print(f"App without reviews {app_id} already exists in database.")
        return ALREADY_EXISTS, query_count
    
    if not exists:
        while retry and not exists:
            try:
                response = request("GET", "https://store.steampowered.com/api/appdetails", params={"appids": app_id, "cc": "us", "l": "english"})
                query_count = check_rate_limit(query_count)
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

        if len(response.text) == 0:
            # example: https://store.steampowered.com/api/appdetails?appids=2124470
            # it exists in SteamDB and the store, but the API returns an empty response
            print(f"Empty response for faulty app ID {app_id}")
            return FAULTY, query_count
        appdata = json.loads(response.text)
        
        if appdata[app_id]["success"]:
            # First, check if this is a game
            if only_games and "type" in appdata[app_id]["data"] and\
                not (appdata[app_id]["data"]["type"] == "game"
                    or appdata[app_id]["data"]["type"] == "mod"
                    or appdata[app_id]["data"]["type"] == "demo"):
                if verbose:
                    print("Skipping non-game: " + appdata[app_id]["data"]["name"])
                return SKIPPED, query_count
            else: name = appdata[app_id]["data"]["name"]
        else:
            print(f"Error for app ID {app_id}: " + response.text)
            return ERROR, query_count
    else:
        name = game_data[1]
    # Then, check if this game has reviews
    if reviews:
        if verbose:
            print("Getting reviews for " + name)
        request_params['cursor'] = '*'
        review_dict, query_count = steamreviews.download_reviews_for_app_id(int(app_id),
                                                                        chosen_request_params=request_params,
                                                                        query_count=query_count, 
                                                                        verbose=True)
        query_summary = review_dict["query_summary"]
    else:
        if verbose:
            print("Getting review summary for " + name)
        _, query_summary, query_count = steamreviews.download_reviews.download_the_full_query_summary(app_id, query_count, request_params)
    
    if not exists:
        process_game_data(app_id, appdata[app_id]["data"], query_summary)
    
    if reviews: # we need to execute this after process_game_data, because of the FK constraint
        process_game_reviews(app_id, review_dict["reviews"])
        mark_as_processed(app_id) # it's only fully processed when the reviews are processed
    if verbose:
        print("App ID: " + app_id + " done.")
    # NOTE: we should probably check the rate limits here, but we're ~10 requests under Steam official limits
    return SUCCESS, query_count

if __name__ == "__main__":
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