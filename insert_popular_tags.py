from requests import get
import json
from database import *

lang = "english"  # future work: language is shared through config.py
popular_tags_url = "https://store.steampowered.com/tagdata/populartags/" + lang

def get_popular_tags():
    response = get(popular_tags_url)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print("Error: status code {}".format(response.status_code))
        return None

def insert_popular_tags():
    popular_tags = get_popular_tags()
    if popular_tags:
        for tag in popular_tags:
            insert_tag(tag)

if __name__ == "__main__":
    print("Downloading and inserting popular tags...")
    insert_popular_tags()
    print("Done.")
