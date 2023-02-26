
from steam import Steam
from decouple import config, UndefinedValueError
import time
from collections import deque
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
# These steam API rate limits still give headroom for the steamreviews library and my own calls to work
# rate limits per day are 100.000 queries, so 250 queries every 5 minutes should be fine, 
# specially if we have headroom for ~347 queries per 5 minutes (69.4 queries per minute)
# either way, to be more precise we can just do it per minute, and add 10 seconds of headroom
_rate_limits = {
    "max_num_queries": 66,
    "cooldown": (60),  # 60 secs for steamreviews
    "cooldown_bad_gateway": 10,  # arbitrary value to tackle 502 Bad Gateway due to saturated servers (during sales)
}

def get_steam_api_rate_limits():
    return _rate_limits

max_num_queries = _rate_limits["max_num_queries"]
cooldown = _rate_limits["cooldown"]
timestamp_queue = deque(maxlen=max_num_queries + 1)

def check_rate_limit(count):
    timestamp_queue.appendleft(time.time())
    count = len(timestamp_queue)

    if count > max_num_queries:
        # pop every timestamp that is older than 60 seconds
        popped_time = timestamp_queue.pop()
        elapsed_time = time.time() - popped_time
        while elapsed_time > cooldown:
            popped_time = timestamp_queue.pop()
            elapsed_time = time.time() - popped_time

        count = len(timestamp_queue)
        if count >= max_num_queries:
            # now empty the query and get the first timestamp
            popped_time = timestamp_queue.pop()

            wait_time = cooldown - (time.time() - popped_time)
            print(f"Waiting {wait_time} seconds to avoid rate limit...")
            time.sleep(wait_time)
            count -= 1
    return count