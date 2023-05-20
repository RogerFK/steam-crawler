# steam-crawler

A crawler that uses [steamreviews](https://pypi.org/project/steamreviews/) to gather users.

Requires `mysql-python-connector` and `Scrapy` if you need to scrap tags.

The database schema is provided. Documentation is kept at a minimum, but may be improved if asked to.

## Getting started

1. Create your own virtual environment, or add all requirements by running `python -m pip install -r requirements.txt`. Ensure pip is installed by running `python -m ensurepip` 
1. Query `database_final_schema.sql` to your MySQL to create the database (depends on the platform).
2. Put the games you want to crawl on `appids.txt`.
3. Run `crawl_app_data.py` first.
4. When done, run `crawl_all_player_data.py` to get all games owned for public players. Doesn't delete players.

`crawl_all_player_data.bat` expects your virtual environment to be put into the `env` folder and uses Windows' venv folder structure.
