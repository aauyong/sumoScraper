# Sumo Scraper

This project is a set of scripts used to parse and scrape the [SumoDB website]([https://](http://sumodb.sumogames.de/Default.aspx)) and the [official Japan Sumo Association website](https://sumo.or.jp/En/) for past and current data, respectively, on Sumo bouts and tournaments (Bashos). The scripts are broken up into three types: Scrapers, Updaters, and Builders. Scrapers gather historical data and/or data stored on

For global settings, such as save locations and reads, those settings can be altered in the settings.ini file.

## Scrapers

The scraper files,profileScraper.py, resultsScraper.py, matchupScraper.py, scrape historical results from SumoDB.

### Profile Scraper (profileScraper.py)

Scrapes biological data and identification numbers for each and every documented rikishi, records it into a single CSV file.

1. id - Id number used by Sumodb
2. shikona - First name of the chosen rikishi title
3. full shikona - Full name of the chosen rikishi title
4. real name - Rikishi's real name
5. hatsu - Rikishi's debut basho
6. intai - Rikishi's retirement basho
7. birth - Birth date
8. shusshin - Birth Location
9. heya - Stable of the Rikishi

Usage :: python profileScraper.py \<Write Option> \<Id File Path>

Write Option: The write mode option, either write ('w') or append ('a') to the save destination file

Id File Path: The filepath for a file containing specific ids to scan. If none is provided, then the set of possible id numbers will be scraped.

### Results Scraper (resultsSCraper.py)

Scrapes through every single documented rikishi and records their win-loss-absent record and biological data. Each wrestler has their data written into its own csv filed labeled with their SumoDB number. Notably, as they are not recorded as such, playoffs are not listed

1. Basho - Basho in the format YYYY.MM
2. Shikona - Name of the rikishi at the time of the basho
3. Name - Full Name of the rikishi at the time of the basho
4. Rank
5. Record_Str - A string of 15 characters that represents all 15 days of the basho, with each character representing that days events. 'O' is a win, 'X' is a loss, 'A' is absent, and 'Z' is a win due to an absence.
6. W - Wins at the Basho
7. L - Losses at the basho
8. A - Absences at the basho
9. Award - Yusho, Jun-Yusho, Kinboshi, or any of the special awards
10. Height - Recorded height at the time. Since it is not recorded for each basho, it may not exist (DNE)
11. Weight - Recorded weight at the time. See Height

### Matchup Scraper (MatchupScraper.py)

Scrapes data ba