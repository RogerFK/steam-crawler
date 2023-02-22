"""
This script crawls game data for a single user.
Author: Jorge González
Date: 2023-02-10
"""

import json
import threading
import time
from steam import Steam
from decouple import config, UndefinedValueError
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

def get_user_data(user_id):
    response = steam.users.get_owned_games(user_id)
    print(response)
#    for keys,values in response.items():
#        print(keys)
#        print(values)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crawl game data for a single user.")
    parser.add_argument("user", help="Steam ID of the user to crawl. Can be a vanity URL or a Steam ID.")
    args = parser.parse_args()
    for i in range(0, 2):
        get_user_data(args.user)
        time.sleep(0.3)

