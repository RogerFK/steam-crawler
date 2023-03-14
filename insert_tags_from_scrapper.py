import pandas as pd
from database import *
from exceptions import *

def check_duplicate_appids(df_gametags: pd.DataFrame):
    # check for duplicate appids
    appdict = dict()
    status = True
    for idx, row in df_gametags.iterrows():
        if row['appid'] == 'app': # error
            continue
        if row['appid'] in appdict:
            current = (row['name'], row['tags'])
            if current != appdict[row['appid']]:
                print("Error: duplicate appid with different values found: " + row['appid'])
                print("Current: " + str(current))
                print("Previous: " + str(appdict[row['appid']]))
                status = False
        else:
            appdict[row['appid']] = (row['name'], row['tags'])
    return status

def insert_tags_from_scrapper(filename):
    try:
        tags = pd.read_json(filename, lines=True)
        tags = tags.drop_duplicates(subset='appid', keep='first').set_index('appid')
    except FileNotFoundError:
        print(filename + " not found.")
        return
    except ValueError:
        print("Error: " + filename + " is not a valid JSON Lines file.")
        return
    
    requires_manual_intervention = []
    for appid, row in tags.iterrows():

        if appid == 'app' or row is None: # error
            continue

        if not game_exists(appid):
            # first try to get the appid, since it might come from a redirect, like Total War: Shogun 2
            try:
                print("Game with appid not inside the database (redirects, betas, etc.): " + row['name'] + " (" + str(appid) + ")")
                gdata = get_game_data_from_name(row['name'])
                if gdata is None:
                    raise RequiresManualIntervention([], row['name'], "No appid found for game " + row['name'])
                appid = int(gdata[0])
            except RequiresManualIntervention as e:
                print("Unambiguous appid returned for game with appid not inside the database (redirects, betas, etc.): " + e.name + " (" + str(e.appids) + ")")
                requires_manual_intervention += (e.name, e.appids)
                continue

        insert_game_tags(appid, row['tags'])
    
    if len(requires_manual_intervention) > 0:
        print("Manual intervention required for the following games:")
        for game in requires_manual_intervention:
            print(game.name + ": " + str(game.appids))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="Filename of the JSON Lines file to be inserted")
    args = parser.parse_args()
    df_gametags = pd.read_json(args.filename, lines=True)
    if check_duplicate_appids(df_gametags):
        print("Inserting tags from " + args.filename + "...")
        insert_tags_from_scrapper(args.filename)
        print("Done.")
    else:
        print("Error: duplicate appids with different values found. Manual review required. Aborting.")
        exit(-1)
