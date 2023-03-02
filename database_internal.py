import mysql.connector
import time

# Diagram of the database
# https://dbdiagram.io/d/63f6302d296d97641d82f22a

connection = mysql.connector.connect(
  host="localhost",
  user="root",
  password="root",
  database="steam_tfg_jgg"
)
cur = connection.cursor()

_insert_player_data_cursor = connection.cursor(prepared=True)
_fetch_player_data_cursor = connection.cursor(prepared=True)

_insert_player_data_stmt = "INSERT INTO player_data "\
    "(steamid, personaname, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, num_reviews, visibility) VALUES "\
    "(?, ?, FROM_UNIXTIME(?), ?, ?, ?, ?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE "\
    "personaname = VALUES(personaname), "\
    "lastlogoff = FROM_UNIXTIME(VALUES(lastlogoff)), "\
    "commentpermission = VALUES(commentpermission), "\
    "primaryclanid = VALUES(primaryclanid), "\
    "timecreated = VALUES(timecreated), "\
    "loccountrycode = VALUES(loccountrycode), "\
    "locstatecode = VALUES(locstatecode), "\
    "loccityid = VALUES(loccityid), "\
    "num_games_owned = VALUES(num_games_owned), "\
    "num_reviews = VALUES(num_reviews), "\
    "visibility = VALUES(visibility);"

_update_player_data_numgames_from_review_stmt = "UPDATE player_data "\
    "SET num_games_owned = ?, "\
    "num_reviews = ?, "\
    "date_retrieved = CURRENT_TIMESTAMP "\
    "WHERE steamid = ?;"

_update_player_data_num_reviews_stmt = "UPDATE player_data "\
    "SET num_reviews = ?, "\
    "date_retrieved = CURRENT_TIMESTAMP "\
    "WHERE steamid = ?;"

_insert_player_data_from_crawl_stmt = "INSERT INTO player_data "\
    "(steamid, personaname, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, visibility) VALUES "\
    "(?, ?, FROM_UNIXTIME(?), ?, ?, ?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE "\
    "personaname = VALUES(personaname), "\
    "lastlogoff = FROM_UNIXTIME(VALUES(lastlogoff)), "\
    "commentpermission = VALUES(commentpermission), "\
    "primaryclanid = VALUES(primaryclanid), "\
    "timecreated = VALUES(timecreated), "\
    "loccountrycode = VALUES(loccountrycode), "\
    "locstatecode = VALUES(locstatecode), "\
    "loccityid = VALUES(loccityid), "\
    "num_games_owned = VALUES(num_games_owned), "\
    "visibility = VALUES(visibility);"

_update_player_data_from_review_stmt = "UPDATE player_data "\
    "SET personaname = ?, "\
    "lastlogoff = FROM_UNIXTIME(?), "\
    "commentpermission = ?, "\
    "primaryclanid = ?, "\
    "timecreated = FROM_UNIXTIME(?), "\
    "loccountrycode = ?, "\
    "locstatecode = ?, "\
    "loccityid = ?, "\
    "num_games_owned = ?, "\
    "visibility = ?, "\
    "date_retrieved = CURRENT_TIMESTAMP "\
    "WHERE steamid = ?;"

_fetch_player_data_stmt = "SELECT steamid, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, num_reviews, visibility "\
    "FROM player_data WHERE steamid = ?;"

def internal_insert_player_data(steamid, personaname, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, num_reviews, visibility):
    if lastlogoff is None or lastlogoff == 0:
        lastlogoff = 1 # 1970-01-01 00:00:01, weird MariaDB design
    _insert_player_data_cursor.execute(_insert_player_data_stmt, (steamid, personaname, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, num_reviews, visibility))


def internal_get_player(steamid):
    _fetch_player_data_cursor.execute(_fetch_player_data_stmt, (steamid,))
    return _fetch_player_data_cursor.fetchone()

def internal_update_player_data(steamid, personaname, visibility, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned):
    if lastlogoff is None or lastlogoff == 0:
        lastlogoff = 1 # 1970-01-01 00:00:01, weird MariaDB design
    _insert_player_data_cursor.execute(_update_player_data_from_review_stmt, (personaname, lastlogoff, commentpermission, primaryclanid, timecreated, loccountrycode, locstatecode, loccityid, num_games_owned, visibility, steamid))

def internal_insert_partial_player_data(steamid, num_games_owned, num_reviews):
    internal_insert_player_data(steamid, None, None, None, None, None, None, None, None, num_games_owned, num_reviews, None)

_get_unprocessed_players_cursor = connection.cursor(prepared=True)

_get_unprocessed_players_stmt = "SELECT steamid FROM player_data WHERE visibility IS NULL ORDER BY num_games_owned LIMIT 100;"

def internal_get_unprocessed_players():
    _get_unprocessed_players_cursor.execute(_get_unprocessed_players_stmt)
    return _get_unprocessed_players_cursor.fetchall()

_insert_game_details_cursor = connection.cursor(prepared=True)

_insert_game_details_stmt = "INSERT INTO game_details "\
    "(appid, name, required_age, is_free, controller_support, has_demo, price_usd, mac_os, positive_reviews, negative_reviews, total_reviews, has_achievements, release_date, coming_soon) "\
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE "\
    "name = VALUES(name), "\
    "required_age = VALUES(required_age), "\
    "is_free = VALUES(is_free), "\
    "controller_support = VALUES(controller_support), "\
    "has_demo = VALUES(has_demo), "\
    "price_usd = VALUES(price_usd), "\
    "mac_os = VALUES(mac_os), "\
    "positive_reviews = VALUES(positive_reviews), "\
    "negative_reviews = VALUES(negative_reviews), "\
    "total_reviews = VALUES(total_reviews), "\
    "has_achievements = VALUES(has_achievements), "\
    "release_date = VALUES(release_date), "\
    "coming_soon = VALUES(coming_soon);"

def internal_insert_game_details(appid, name, required_age, is_free, controller_support, has_demo, price_usd, mac_os, positive_reviews, negative_reviews, total_reviews, has_achievements, release_date, coming_soon):
    _insert_game_details_cursor.execute(_insert_game_details_stmt, (appid, name, required_age, is_free, controller_support, has_demo, price_usd, mac_os, positive_reviews, negative_reviews, total_reviews, has_achievements, release_date, coming_soon))
    # connection.commit()

_insert_game_genres_cursor = connection.cursor(prepared=True)

_insert_game_genres_stmt = "INSERT IGNORE INTO game_genres "\
    "(appid, genre_id) "\
    "VALUES (?, ?);"

_insert_genre_cursor = connection.cursor(prepared=True)

_insert_genre_stmt = "INSERT IGNORE INTO genres VALUES (?, ?);"

def internal_insert_game_genres(appid, genres):
    for genre in genres:
        _insert_genre_cursor.execute(_insert_genre_stmt, (genre["id"], genre["description"]))
        _insert_game_genres_cursor.execute(_insert_game_genres_stmt, (appid, genre["id"]))
    # connection.commit()

_insert_game_categories_cursor = connection.cursor(prepared=True)

_insert_game_categories_stmt = "INSERT IGNORE INTO game_categories "\
    "(appid, category_id) "\
    "VALUES (?, ?);"

_insert_category_cursor = connection.cursor(prepared=True)

_insert_category_stmt = "INSERT IGNORE INTO categories VALUES (?, ?);"

def internal_insert_game_categories(appid, categories):
    for category in categories:
        _insert_category_cursor.execute(_insert_category_stmt, (category["id"], category["description"]))
        _insert_game_categories_cursor.execute(_insert_game_categories_stmt, (appid, category["id"]))
    # connection.commit()

_insert_game_developers_cursor = connection.cursor(prepared=True)

_insert_game_developers_stmt = "INSERT IGNORE INTO game_developers "\
    "(appid, developer_id) "\
    "VALUES (?, ?);"

_get_developer_id_cursor = connection.cursor(prepared=True)

_get_developer_id_stmt = "SELECT developer_id FROM developers WHERE developer_name = ?;"

_insert_developer_cursor = connection.cursor(prepared=True)

_insert_developer_stmt = "INSERT INTO developers (developer_name) VALUES (?);"

_get_next_autoincrement_id_cursor = connection.cursor(prepared=True)

_get_next_autoincrement_id_stmt = "SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'steam_tfg_jgg' AND TABLE_NAME = 'developers';"

def internal_insert_game_developers(appid, developers: list[str]):
    for developer in developers:
        _get_developer_id_cursor.execute(_get_developer_id_stmt, (developer,))
        developer_id = _get_developer_id_cursor.fetchone()
        if developer_id is None: # doesn't exist
            _get_next_autoincrement_id_cursor.execute(_get_next_autoincrement_id_stmt)
            developer_id = _get_next_autoincrement_id_cursor.fetchone()
            _insert_developer_cursor.execute(_insert_developer_stmt, (developer,))
            connection.commit() # we need commit for the next row to not violate the foreign key constraint
        developer_id = developer_id[0]
        _insert_game_developers_cursor.execute(_insert_game_developers_stmt, (appid, developer_id))
    # connection.commit()

_insert_game_publishers_cursor = connection.cursor(prepared=True)

_insert_game_publishers_stmt = "INSERT IGNORE INTO game_publishers "\
    "(appid, publisher_id) "\
    "VALUES (?, ?);"

_get_publisher_id_cursor = connection.cursor(prepared=True)

_get_publisher_id_stmt = "SELECT publisher_id FROM publishers WHERE publisher_name = ?;"

_insert_publisher_cursor = connection.cursor(prepared=True)

_insert_publisher_stmt = "INSERT INTO publishers (publisher_name) VALUES (?);"

_get_next_autoincrement_id_pub_cursor = connection.cursor(prepared=True)

_get_next_autoincrement_id_pub_stmt = "SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'steam_tfg_jgg' AND TABLE_NAME = 'publishers';"

def internal_insert_game_publishers(appid, publishers: list[str]):
    for publisher in publishers:
        _get_publisher_id_cursor.execute(_get_publisher_id_stmt, (publisher,))
        publisher_id = _get_publisher_id_cursor.fetchone()
        if publisher_id is None:
            _get_next_autoincrement_id_pub_cursor.execute(_get_next_autoincrement_id_pub_stmt)
            publisher_id = _get_next_autoincrement_id_pub_cursor.fetchone()
            _insert_publisher_cursor.execute(_insert_publisher_stmt, (publisher,))
            connection.commit() # we need commit for the next row to not violate the foreign key constraint
        publisher_id = publisher_id[0]
        _insert_game_publishers_cursor.execute(_insert_game_publishers_stmt, (appid, publisher_id))
    # connection.commit()

_insert_player_game_reviews_cursor = connection.cursor(prepared=True)

_insert_player_game_reviews_stmt = "INSERT INTO player_game_reviews "\
    "(recommendationid, steamid, appid, voted_up, timestamp_created, timestamp_updated, playtime_at_review, received_for_free, steam_purchase, written_during_early_access) "\
    "VALUES (?, ?, ?, ?, FROM_UNIXTIME(?), FROM_UNIXTIME(?), ?, ?, ?, ?) ON DUPLICATE KEY UPDATE "\
    "voted_up = VALUES(voted_up), "\
    "timestamp_created = VALUES(timestamp_created), "\
    "timestamp_updated = VALUES(timestamp_updated), "\
    "playtime_at_review = VALUES(playtime_at_review), "\
    "received_for_free = VALUES(received_for_free), "\
    "steam_purchase = VALUES(steam_purchase), "\
    "written_during_early_access = VALUES(written_during_early_access);"

def internal_insert_player_game_review(recommendationid, steamid, appid, voted_up, timestamp_created, timestamp_updated, playtime_at_review, playtime_forever,  received_for_free, steam_purchase, written_during_early_access, last_played):
    _insert_player_game_reviews_cursor.execute(_insert_player_game_reviews_stmt, (recommendationid, steamid, appid, voted_up, timestamp_created, timestamp_updated, playtime_at_review, received_for_free, steam_purchase, written_during_early_access))
    internal_insert_player_game(steamid, appid, playtime_forever, None, None, None, None, last_played)
    # connection.commit()

_insert_player_games_cursor = connection.cursor(prepared=True)

_insert_player_games_stmt = "INSERT INTO player_games "\
    "(steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, achievement_percentage, rtime_last_played) "\
    "VALUES (?, ?, ?, ?, ?, ?, ?, FROM_UNIXTIME(?)) ON DUPLICATE KEY UPDATE "\
    "playtime_forever = VALUES(playtime_forever), "\
    "playtime_windows = VALUES(playtime_windows), "\
    "playtime_mac = VALUES(playtime_mac), "\
    "playtime_linux = VALUES(playtime_linux), "\
    "achievement_percentage = VALUES(achievement_percentage), "\
    "rtime_last_played = VALUES(rtime_last_played);"

def internal_insert_player_game(steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, achievement_percentage, rtime_last_played):
    rtime_last_played = rtime_last_played if rtime_last_played > 0 else 1 # apparently MySQL's timestamps go from 1970-01-01 00:00:01 to 2038-01-19 03:14:07, 1970-01-01 00:00:00 isn't valid
    _insert_player_games_cursor.execute(_insert_player_games_stmt, (steamid, appid, playtime_forever, playtime_windows, playtime_mac, playtime_linux, achievement_percentage, rtime_last_played))
    # connection.commit()

_insert_candidate_games_cursor = connection.cursor(prepared=True)

_insert_candidate_games_stmt = "INSERT INTO candidate_appids (appid) VALUES (?) ON DUPLICATE KEY UPDATE count = count + 1;"

def internal_insert_or_update_candidate_game(appid):
    _insert_candidate_games_cursor.execute(_insert_candidate_games_stmt, (appid,))
    # connection.commit()

_insert_processed_appids_cursor = connection.cursor(prepared=True)

_insert_processed_appids_stmt = "INSERT INTO processed_appids (appid) VALUES (?) ON DUPLICATE KEY UPDATE last_updated = CURRENT_TIMESTAMP;"

_delete_candidate_games_cursor = connection.cursor(prepared=True)

_delete_candidate_games_stmt = "DELETE FROM candidate_appids WHERE appid = ?;"

def internal_insert_processed_appid(appid):
    _insert_processed_appids_cursor.execute(_insert_processed_appids_stmt, (appid,))
    _delete_candidate_games_cursor.execute(_delete_candidate_games_stmt, (appid,))
    # connection.commit()

_get_candidate_games_cursor = connection.cursor(prepared=True)

_get_candidate_games_stmt = "SELECT appid FROM candidate_appids ORDER BY count DESC LIMIT ?;"
def internal_get_candidate_games(limit):
    _get_candidate_games_cursor.execute(_get_candidate_games_stmt, (limit,))
    candidates = _get_candidate_games_cursor.fetchall()
    return [candidate[0] for candidate in candidates]

get_game_data = connection.cursor(prepared=True)

get_game_data_stmt = "SELECT * FROM game_details WHERE appid = ?;"

def internal_get_game_data(appid):
    get_game_data.execute(get_game_data_stmt, (appid,))
    return get_game_data.fetchone()