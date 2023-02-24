from database_internal import *
import re
debug = False

def is_processed(appid):
    cur.execute("SELECT appid FROM processed_appids WHERE appid = %s;", (appid,))
    return cur.fetchone() is not None

def add_dead_hidden_game(appid):
    cur.execute("INSERT INTO game_details (appid, name) VALUES (%s, 'DEAD_HIDDEN_GAME');", (appid,))
    connection.commit()

def process_game_data(appid, appdetails, query_summary):
    print(f"Inserting game with appid {appid} into the database")
    name = appdetails["name"]
    # EA's Mass Effect Legendary Edition has a required_age of 17+ instead of just 17, this regex fixes that
    required_age = int(re.sub(r"\D", "", str(appdetails["required_age"]))) if "required_age" in appdetails else 0
    is_free = appdetails["is_free"]
    has_demo = "demos" in appdetails
    price_usd = int(appdetails["price_overview"]["final"]) if "price_overview" in appdetails else 0
    mac_os = appdetails["platforms"]["mac"]
    positive_reviews = query_summary["total_positive"]
    negative_reviews = query_summary["total_negative"]
    total_reviews = query_summary["total_reviews"]
    has_achievements = appdetails["achievements"]["total"] > 0 if "achievements" in appdetails else False
    release_date = appdetails["release_date"]["date"] if "release_date" in appdetails else None
    coming_soon = appdetails["release_date"]["coming_soon"] if "release_date" in appdetails else False
    categories = appdetails["categories"] if "categories" in appdetails else []
    genres = appdetails["genres"] if "genres" in appdetails else []
    controller_support = 2 if "controller_support" in appdetails else 1 if {"id": 18, "description": "Partial Controller Support"} in categories else 0
    developers = appdetails["developers"] if "developers" in appdetails else []
    publishers = appdetails["publishers"] if "publishers" in appdetails else []
    # print all variables for debugging purposes
    if debug:
        print(f"appid: {appid}")
        print(f"name: {name}")
        print(f"required_age: {required_age}")
        print(f"is_free: {is_free}")
        print(f"controller_support: {controller_support}")
        print(f"has_demo: {has_demo}")
        print(f"price_usd: {price_usd}")
        print(f"mac_os: {mac_os}")
        print(f"positive_reviews: {positive_reviews}")
        print(f"negative_reviews: {negative_reviews}")
        print(f"total_reviews: {total_reviews}")
        print(f"has_achievements: {has_achievements}")
        print(f"release_date: {release_date}")
        print(f"coming_soon: {coming_soon}")
        print(f"categories: {categories}")
        print(f"genres: {genres}")
        print(f"developers: {developers}")
        print(f"publishers: {publishers}")
    # insert into database
    internal_insert_game_details(appid, name, required_age, is_free, controller_support, has_demo, price_usd, mac_os, positive_reviews, negative_reviews, total_reviews, has_achievements, release_date, coming_soon)
    internal_insert_game_genres(appid, genres)
    internal_insert_game_categories(appid, categories)
    # TODO: delete developers and publishers before inserting, in case they changed (Ready or Not (T17 -> VOID), WW3...)
    internal_insert_game_developers(appid, developers)
    internal_insert_game_publishers(appid, publishers)
    connection.commit()

def process_game_reviews(app_id, review_dict):
    """Processes game reviews and inserts partial information into player_games table.

    Args:
        app_id (str | int): the app id of the game
        review_dict (dict): the dictionary containing the review data, returned from steamreviews download method
    """
    # print(f"Inserting game reviews with appid {app_id} into the database")
    for recommendationid, review in review_dict.items():
        try:
            steamid = review["author"]["steamid"]
            num_games_owned = review["author"]["num_games_owned"]
            num_reviews = review["author"]["num_reviews"]
            process_partial_player_from_review(steamid, num_games_owned, num_reviews)
            playtime_at_review = review["author"]["playtime_at_review"] if "playtime_at_review" in review["author"] else 0
            playtime_forever = review["author"]["playtime_forever"] if "playtime_forever" in review["author"] else 0
            voted_up = review["voted_up"]
            timestamp_created = review["timestamp_created"]
            timestamp_updated = review["timestamp_updated"]
            received_for_free = review["received_for_free"]
            steam_purchase = review["steam_purchase"]
            written_during_early_access = review["written_during_early_access"]
            last_played = review["author"]["last_played"]
        except Exception as e:
            print(f"Error processing review with recommendationid {recommendationid}: {e}")
            print(review)
            continue
        process_game_review(recommendationid, steamid, app_id, voted_up, timestamp_created, timestamp_updated, playtime_at_review, playtime_forever,  received_for_free, steam_purchase, written_during_early_access, last_played)
    connection.commit()

def process_partial_player_from_review(steamid, num_games_owned, num_reviews):
    #print(f"Inserting player with steamid {steamid} into the database")
    internal_insert_partial_player_data(steamid, num_games_owned, num_reviews)

def mark_as_processed(appid):
    print(f"Marking appid {appid} as processed")
    internal_insert_processed_appid(appid)
    connection.commit()

def process_game_review(recommendationid, steamid, appid, voted_up, timestamp_created, timestamp_updated, playtime_at_review, playtime_forever,  received_for_free, steam_purchase, written_during_early_access, last_played):
    #print(f"Inserting player game review with recommendationid {recommendationid} into the database")
    internal_insert_player_game_review(recommendationid, steamid, appid, voted_up, timestamp_created, timestamp_updated, playtime_at_review, playtime_forever,  received_for_free, steam_purchase, written_during_early_access, last_played)

def get_100_unprocessed_players():
    return internal_get_unprocessed_players()

def game_exists(appid):
    return internal_get_game_data(appid) is not None

def process_steam_user(steamid, personaname, visibility, num_games_owned = 0, lastlogoff=None, commentpermission=None, primaryclanid=None, timecreated=None, loccountrycode=None, locstatecode=None, loccityid=None):
    player_row = internal_get_player(steamid)
    if player_row is not None:
        # maybe we already got num_games_owned from reviews, don't update that value
        # i think this check is redundant, but better safe than sorry
        if num_games_owned == 0 and player_row[10] is not None:
            num_games_owned = player_row[10]
        internal_update_player_data(steamid, personaname, visibility, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned)
    else:
        # we can't really know how many reviews they have which is why we set it to 0
        internal_insert_player_data(steamid, personaname, visibility, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, num_reviews=0)
    connection.commit()
    print("Processed player", steamid)

def insert_player_game_data(steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, rtime_last_played, achievement_percentage=-1):
    insert_candidate_game(appid)
    internal_insert_player_game(steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, achievement_percentage, rtime_last_played)
    connection.commit()

def insert_candidate_game(appid):
    #print(f"Inserting candidate game with appid {appid} into the database")
    internal_insert_or_update_candidate_game(appid)
    connection.commit()
