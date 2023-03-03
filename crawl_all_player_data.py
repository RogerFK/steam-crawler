"""
This script crawls game data for every player from the database.
Author: Jorge González
Date: 2023-02-20
"""

import json
import time
import requests
import steamreviews
from database import *
import os
from crawl_app_data import get_app_data, ERROR, SUCCESS, ALREADY_EXISTS, FULLY_PROCESSED, SKIPPED, FAULTY
from config import steam, check_rate_limit, KEY

def crawl_player_data(query_count=0, reviews=False, only_games=True, verbose=False):
    unprocessed_players = get_100_unprocessed_players()
    while len(unprocessed_players) > 0:
        start_time = time.time()
        steam_ids = [str(player[0]) for player in unprocessed_players]
        while True:
            try:
                response = steam.users.get_user_details(",".join(steam_ids), single=False)
                query_count = check_rate_limit(query_count)
                if "players" in response:
                    break
                else:
                    print("Error while requesting user details, no players. Waiting 10 seconds: ")
                    print(response)
                    time.sleep(10)
            except Exception as e:
                print("Exception while requesting user details. Waiting 10 seconds: ")
                print(e)
                time.sleep(10)
        players = response["players"]
        for player in players:
            steamid = player["steamid"]
            if player["communityvisibilitystate"] == 1 or player["communityvisibilitystate"] == 2:
                if verbose:
                    print("Private/Friends only profile, setting basic player profile...")
                # TODO: Mark visibility as 0 in database
                # api: process_steam_user(steamid, personaname, visibility, num_games_owned = 0, commentpermission=None, primaryclanid=None, timecreated=None, loccountrycode=None, locstatecode=None, loccityid=None):
                process_steam_user(steamid, player["personaname"], 0, 0)
                continue
            
            commentpermission = player["commentpermission"] if "commentpermission" in player else None
            primaryclanid = player["primaryclanid"] if "primaryclanid" in player else None
            timecreated = player["timecreated"] if "timecreated" in player else None
            loccountrycode = player["loccountrycode"] if "loccountrycode" in player else None
            locstatecode = player["locstatecode"] if "locstatecode" in player else None
            loccityid = player["loccityid"] if "loccityid" in player else None
            while True:
                try:
                    resp = requests.request(
                        "get",
                        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/",
                        params={"steamid": steamid,
                                "include_appinfo": False,
                                "include_played_free_games": True,
                                "key": KEY},
                    )
                    query_count = check_rate_limit(query_count)
                    if resp.status_code == 200: # I didn't trust the API to return stuff properly when rate limited
                        owned_games = json.loads(resp.text)["response"]
                        break
                    else:
                        print("Error while requesting owned games. Waiting 3 seconds: ")
                        print(resp.text)
                        time.sleep(3)
                except Exception as e:
                    print("Exception while requesting user details. Waiting 10 seconds: ")
                    print(e)
                    time.sleep(10)
            
            if "games" not in owned_games:
                if verbose:
                    print("Game list is private, skipping...")
                process_steam_user(steamid, player["personaname"], 1, 0, 
                                   commentpermission=commentpermission, 
                                   primaryclanid=primaryclanid, 
                                   timecreated=timecreated,
                                   loccountrycode=loccountrycode, 
                                   locstatecode=locstatecode,
                                   loccityid=loccityid)
                continue
            
            visible_playtime = False
            for game in owned_games["games"]:
                appid = game["appid"]
                success = SUCCESS

                if not game_exists(appid):
                    if verbose:
                        print(f"{appid} doesn't exist in database, crawling...")
                    success, query_count = get_app_data(str(appid), reviews=reviews, query_count=query_count, only_games=only_games, verbose=verbose)
                visible_playtime |= game["playtime_forever"] > 0
                if success == ERROR:
                    if verbose:
                        print("Error while crawling game, adding as 'DEAD_HIDDEN_GAME' with no info...")
                    # NOTE: this is specially useful to see 'if you used to play appid X and you now play appid Y, others might like appid Y'
                    # for example: Project Cars 1 and 2 are dead, but you might like Project Cars 3 without genre context
                    # also PUBG Test Server, Realm Royale Public Test, etc. are hidden
                    add_dead_hidden_game(appid)
                elif success == SKIPPED:
                    if verbose:
                        print("Non-game/mod skipped, skipping...")
                    continue
                elif success == FAULTY:
                    if verbose:
                        print("Faulty game, inserting as faulty with 'FAULTY_GAME' with no info...")
                    add_faulty_game(appid)
                # insert_player_game_data(steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, rtime_last_played)
                insert_player_game_data(steamid, appid, game["playtime_forever"], game["playtime_windows_forever"], game["playtime_mac_forever"], game["playtime_linux_forever"], game["rtime_last_played"])

            process_steam_user(steamid, player["personaname"], 2 if visible_playtime else 3, owned_games["game_count"],
                               commentpermission=commentpermission, 
                               primaryclanid=primaryclanid, 
                               timecreated=timecreated,
                               loccountrycode=loccountrycode, 
                               locstatecode=locstatecode,
                               loccityid=loccityid)
        print(f"Processed 100 players ({steam_ids}), Time to process batch:", time.time() - start_time, "seconds")
        unprocessed_players = get_100_unprocessed_players()
    
    return query_count
    

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl player data from the database.")
    # optional parameter in case we want new reviews
    parser.add_argument("-r", "--reviews", action="store_true", help="Crawl reviews for every game in the database.")
    # another one for only games
    parser.add_argument("-g", "--only_games", action="store_false", help="Only crawl games, not DLCs or other types of products.")
    args = parser.parse_args()
    print(f"Crawling player data with reviews={args.reviews} and only_games={args.only_games}...")
    crawl_player_data(query_count=0, reviews=args.reviews, only_games=args.only_games)
