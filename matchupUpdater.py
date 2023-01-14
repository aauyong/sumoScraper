
import datetime as dt
from typing import Tuple
import pandas as pd
import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from helpers import *
from bs4 import BeautifulSoup as bs
from bs4.element import Tag

TORIKUMI_URL = "https://sumo.or.jp/EnHonbashoMain/torikumi/{}/{}/"
SAVE_DEST =r"C:\Users\blarg\Documents\SQL Server Management Studio\SumoScripts\newMatchups.csv"

MU_HEADERS = {
    "basho": None,
    "day": None,
    "jsa_id": None,
    # "left_shikona":None,
    "result": None,
    "jsa_opp_id": None,
    # "right_shikona": None,
    "kimarite": None,
    "division": None,
    "match_order": None
}

RESULT_MARKERS_REVERSED = {
    "O": "X",
    "X": "O",
    "Z": "A",
    "A": "Z",
    '-': '-',
    None:None
}

DAYS = range(1, 16)

DIVISIONS = range(1, 7)

SYS_DEFAULTS = {
    'days': None, 'days_end': None
}


def extractDateToBasho(s:str) -> dt.date:
    """***************************************************************************

    Parse a string in the form "{day #} Day Month, Day, Year", and use regex to
    extract the date and reformat it as a basho string in the form "YYYY.MM"

    ### Parameters ###
    * s : string to parse

    ### Return ###
    * Basho String
    ***************************************************************************"""
    pattA = r"Day\s*\d+\s*"
    pattB = r"Day\s+"
    srch = re.search(pattA, s)
    if srch == None:
        srch = re.search(pattB, s)
    s = s[srch.end():].rstrip()
    basho = dt.datetime.strptime(s, "%B %d, %Y").strftime("%Y.%m")
    return basho
# END OF extractDate
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def getDayMatchups(driver: webdriver.Firefox, division: int = 1, day: int = 1) -> list():
    """***************************************************************************

    Parse the torikumi page for a specific day and division. Turns rows into
    id and opp_id, putting winner on id. Gathers kimarite, and counts match
    for day order.

    ### Parameters ###
    * division : division in enumerated form to parse
    * day : matchup day to parse

    ### Return ###
    * None
    ***************************************************************************"""
    driver_waiter = WebDriverWait(driver, timeout=10)

    url = TORIKUMI_URL.format(division, day)
    driver.get(url)
    try:
        driver_waiter.until(ec.all_of(
            ec.url_matches(url)
            ,ec.text_to_be_present_in_element(
                ("css selector", "#dayHead"), 'Day')
            ,ec.presence_of_element_located(
                ("css selector", "#dayHead"))
            ,ec.presence_of_element_located(
                ("css selector", "#torikumi_table > colgroup"))
        ))
    except TimeoutException as e:
        return None

    soup = bs(driver.page_source, "html.parser")
    try:
        mu_tbl = soup.find("table", id="torikumi_table").find_all("tr")[1:]
        if len(mu_tbl) == 0 \
                and ec.invisibility_of_element(("css selector", "#torikumi_table"))(driver):
            print(f"Cannont find Matchup Table for {division}, day {day}")
            return None
    except AttributeError as e:
        print(f"Cannont find Matchup Table for {division}, day {day}")
        print(e)
        return None

    basho = extractDateToBasho(soup.select_one("#dayHead").text)
    matchups = list()
    for mu_cnt, row in enumerate(mu_tbl):
        if (len(row.find_all("td")) == 0):
            continue  # Skip header row

        d = dict(MU_HEADERS)

        wrestlers = dict(zip(
            ['left', 'right'],
            row.select("td.win:not(.result), td.player"))
        )

        try:
            d["jsa_id"] = parseTorikumiCell(wrestlers['left'])
        except AttributeError:
            print(f"Cannot find a left cell for {mu_cnt+1}")

        try:
            d["jsa_opp_id"] = parseTorikumiCell(wrestlers['right'])
        except AttributeError:
            print(f"Cannot find a right cell for {mu_cnt+1}")

        try:
            d["kimarite"] = row.find("td", class_="decide").text.lstrip().rstrip()
        except AttributeError as e:
            print(f"Cannot find a kimarite cell for {mu_cnt+1}")

        if (d['kimarite']):
            try:
                results = dict(zip(
                    ['left', 'right'],
                    row.select("td.result")
                ))

                if len(results) != 2:
                    raise AttributeError("Wrong number of result cells")

                if results['left'].has_attr("class") and "win" in results['left'].get("class"):
                    d["result"] = 'O' if 'fu' not in d["kimarite"] else 'Z'
                elif results['right'].has_attr("class") and "win" in results['right'].get("class"):
                    d["result"] = 'X' if 'fu' not in d["kimarite"] else 'A'

            except AttributeError as e:
                print(f"Cannot derive result")
                print(e)

        d["match_order"] = mu_cnt + 1
        d["division"] = division

        d["day"] = day
        d["basho"] = basho

        matchups.append(d)
        matchups.append(flipMatchups(d))

    return matchups
# END OF getDayMatchups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def flipMatchups(data: dict) -> dict:
    """***************************************************************************

    Flips the matchup data, puts the loser on the left. Flips id and opp_id, and
    reverses the result. IMportant for SQL importing

    ### Parameters ###
    * data : a dict based on MU_HEADERS

    ### Return ###
    * dict based on MU_HEADERS
    ***************************************************************************"""
    d = dict(data)
    d["jsa_id"], d['jsa_opp_id'] = data["jsa_opp_id"], data["jsa_id"]
    # d['left_shikona'], d['right_shikona'] = d['right_shikona'], d['left_shikona']
    d["result"] = RESULT_MARKERS_REVERSED[data["result"]]
    return d
# END OF flipMatchups
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def matchupDriver(divisions_list:list=list(DIVISIONS), days_l:list=list(DAYS)) -> list:
    """***************************************************************************

    Driver for getting matchups. Parses each division and day provided in the
    args and returns the aggregate data. If no data is scraped for an entire day,
    the function exits, as it assumes no information further information is
    available

    ### Parameters ###
    * divisions_list : List of divisions represented as integers
    * days_l : List of days represented as integers

    ### Return ###
    * List of all matchups
    ***************************************************************************"""
    total_data = list()
    with getHeadlessDriver() as driver:
        for day in days_l:
            day_failure = True
            for div in divisions_list:
                print(f"Parsing Division {div} - Day {day}")
                data = getDayMatchups(driver, div, day)
                if data == None:
                    print(f"No data for Division {div} - Day {day}")
                    continue
                day_failure = False
                total_data.extend(data)

            if day_failure:
                print(f"No data found for entire Day {day}")
                print(f"Returning Data and cleaning up")
                break

    return total_data
# END OF matchupDriver
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def parseTorikumiCell(cell:Tag) -> Tuple[str, str]:
    """***************************************************************************

    Parse a torikumi cell to get the id number and shikona of a wrestler.

    Raises AttributeError

    ### Parameters ###
    * cell : A Tag element containing the appropriate information

    ### Return ###
    * Tuple of the id as a string and the name
    ***************************************************************************"""
    cell_name = cell.find("span", class_="name")
    cell_link = cell_name.find('a')["href"]
    id_ = re.search(r"(\d+)/*\Z", cell_link).groups()[0]
    return id_
# END OF parseCell
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def argValidation(sys_args: dict, usage: str):
    if sys_args['days'] == None:
        sys_args["days"] = 1
        sys_args["days_end"] = 16
        return

    try:
        sys_args["days"] = int(sys_args["days"])
    except ValueError as e:
        print(f"Value for day is not a number")
        print(usage)

    if sys_args["days_end"] == None:
        sys_args["days_end"] = sys_args["days"] + 1
    else:
        try:
            sys_args["days_end"] = int(sys_args["days_end"])
        except ValueError as e:
            print(f"Value for days_end is not a number")
            print(usage)

    try:
        assert sys_args["days"] in range(1, 16), "Day must be between 1 and 15"

        assert sys_args["days_end"] in range(
            2, 17), "Days must be between 2 and 16"

        assert sys_args["days_end"] > sys_args["days"], "Days end must be greater than days"
    except AssertionError as e:
        print(e)
        print(usage)


def main():
    args = SYS_DEFAULTS
    if len(sys.argv) > 1:
        args = readSysArgs(SYS_DEFAULTS.keys())
    else:
        args = SYS_DEFAULTS
    validateArgs(args, SYS_DEFAULTS, argValidation)

    data = list()
    data = matchupDriver(list(DIVISIONS), range(
        args["days"], args["days_end"]))
    df = pd.DataFrame(data=data)
    df.to_csv(
        SAVE_DEST
        , index=False
    )


if __name__ == "__main__":
    main()
