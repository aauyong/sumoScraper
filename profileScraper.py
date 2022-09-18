import os
import pandas as pd
import re
import sys

from bs4 import BeautifulSoup as bs
from helpers import *
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

KAKU_URL = "http://sumodb.sumogames.de/Rikishi_stat.aspx?kaku={}"
PROFILE_URL = 'http://sumodb.sumogames.de/Rikishi.aspx?r={}'
SAVE_DEST = r".\id.csv"

PROFILE_HDRS = (
    "id",
    "shikona",
    "full_shikona",
    "real_name",
    "hatsu",
    "intai",
    "birth",
    "shusshin",
    "heya"
)


def downloadProfiles(write_opt:str='w', id_file:str = None):
    """***************************************************************************

    Downloads profile data from sumodb by parsing through the pages of each
    profile page, accessed with the rikishi's id number as indexed by sumodb.
    Utilizes a failure count; if 10 pages in a row fail to be read, returns False.

    Will write contents to id.csv if cancelled or failed midway

    ### Parameters ###
    * write_opt : file writing option. If 'w' is used, function will write a new
                file. If 'a' is used, function assumes the presence of a previous
                written' id.csv' and will read from it, continuing where it left off.
    * id_file : a file path to a list of ids to read from and use. If not provided
                then ids are scraped from the historical sumo rikishi list
    ***************************************************************************"""
    id_set = set()
    if id_file:
        try:
            assert os.path.isfile(id_file)\
                , f"{id_file} is not a valid file to read from"
        except AssertionError as e:
            print(e)
            return False

        with open(id_file, 'r') as f:
            id_set = set([x.lstrip().rstrip() for x in f.readlines()])
    else:
        id_set = scrapeIdNums()

    if write_opt == 'a':
        profdf = pd.read_csv(SAVE_DEST)
        finished_ids = set(profdf['id'].unique())
        id_set = id_set.difference(finished_ids)

    with getHeadlessDriver() as driver:
        waiter = WebDriverWait(driver, timeout=10)
        prof_data = list()
        failure_cnt = 0
        try:
            for id_ in id_set:
                if failure_cnt > 10:
                    print(f"Too many failures, ending")
                    break
                try:
                    url = PROFILE_URL.format(id_)
                    driver.get(url)
                    waiter.until(ec.url_to_be(PROFILE_URL.format(id_)))
                    print(f"=== {id_} : scraping===")
                    results = scrapeRikishiProfile(driver.page_source, id_)
                    if results:
                        prof_data.append(results)
                        print(f"Success")
                        failure_cnt = 0
                    else:
                        print(f"Failure: {failure_cnt + 1}")
                        failure_cnt += 1
                except TimeoutException:
                    print(f"Timeout Occurred for {id_}")
                    failure_cnt += 1
                    continue
                except AttributeError:
                    print("Failure, attribute error")
                    failure_cnt += 1
                    continue
        except Exception as e:
            print(e)
            return False
        finally:
            profdf = pd.DataFrame(data=prof_data, columns=PROFILE_HDRS)
            profdf.to_csv(SAVE_DEST, index=False, mode=write_opt, header=(write_opt != 'a'))

    return True
# END OF downloadProfiles
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def scrapeIdNums() -> list:
    """***************************************************************************

    Parse through sumodb's rikishi page and scrape out the id numbers of all
    historical rikishi from their links

    ### Parameters ###
    * :

    ### Return ###
    * The id number of every single rikishi in the database
    ***************************************************************************"""
    possibleIdNums = list()
    with getHeadlessDriver() as driver:
        driver_waiter = WebDriverWait(driver, timeout=30)
        for i in range(10):
            i = i + 1
            curr_url = KAKU_URL.format(i)
            driver.get(curr_url)
            try:
                driver_waiter.until(ec.url_to_be(curr_url))
            except TimeoutException as e:
                print(f"Timeout for page {i}")
                print(f"Got {driver.current_url}")
                continue
            try:
                driver_waiter.until(
                    ec.presence_of_element_located
                        (("css selector", "table.rikishidata"))
                )
            except TimeoutException:
                print(f"Timeout for page {i}")
                print(f"Couldn't get loaded table data")
                continue

            soup = bs(driver.page_source, "html.parser")

            table = soup.find("tbody")
            rows = table.find_all("tr")
            for row in rows:
                try:
                    id_tag = row.find("a")
                    rikishi_link = id_tag.get("href")
                    id = int(rikishi_link[rikishi_link.find("r=") + 2:])
                    possibleIdNums.append(id)
                except AttributeError:
                    print(f"issue with {row}")
                    continue
    return set(possibleIdNums)
# END OF scrapeIdNums
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def scrapeRikishiProfile(profile_source:str, id_:int) -> dict:
    """***************************************************************************

    Parse a sumodb webpgae for a given identification number, {x}.

    Scrapes the shikona, full name, hatsu (debut), intai (retirement),
    and birth, and makes sure to format each one properly

    ### Parameters ###
    * id : A rikishi id number to parse

    ### Return ###
    *
    ***************************************************************************"""
    soup = bs(profile_source, "html.parser")

    try:
        print(f"Parsing {id_}")
        full_shikona = soup.find(class_='layoutright').find("h2").text
        yokozuna_patt = r"[\d]+[th|st|rd|nd]* Yokozuna"
        m = re.split(yokozuna_patt, full_shikona)
        full_shikona = m[-1].rstrip().lstrip()
        shikona = full_shikona.split(" ")[0]

        def getNextSiblingOfElement(tag:str, string:str) -> str:
            """***************************************************************
            Helper function to get text of the next element of a given tag
            with string value
            ***************************************************************"""
            s = ""
            try:
                s =  rikishi_data_tbl.find(tag, string=string).nextSibling.text
            except AttributeError:
                print(f"{id_} has no {string}")
            finally:
                return s

        rikishi_data_tbl = soup.find(class_="rikishidata")

        hatsu = getNextSiblingOfElement("td", "Hatsu Dohyo")
        try:
            m = re.split(r"(\d{4}\.\d{2})", hatsu)
            hatsu = m[1].lstrip().rstrip()
        except IndexError:
            print(f"{id_} has a weird hatsu format, {hatsu}")

        intai = getNextSiblingOfElement('td', 'Intai')
        try:
            m = re.split(r"(\d{4}\.\d{2})", intai)
            intai = m[1].lstrip().rstrip()
        except IndexError:
            print(f"{id_} has a weird hatsu format, {intai}")

        birth = getNextSiblingOfElement('td', 'Birth Date')
        birth = birth.replace(",", "")
        if birth.find("(") > -1:
            birth = birth[: birth.find("(")].lstrip().rstrip()
        birth = pd.to_datetime(birth, errors="ignore")
        if (type(birth) != str):
            birth = birth.date()

        shusshin = getNextSiblingOfElement('td', 'Shusshin')
        shusshin = shusshin.replace(",", "").lstrip().rstrip()

        heya = getNextSiblingOfElement('td', 'Heya')

        real_name = getNextSiblingOfElement('td', 'Real Name')
        real_name = real_name.split("-")[0].lstrip().rstrip()

        return dict(zip(
            PROFILE_HDRS,
            [id_,shikona,full_shikona,real_name,hatsu,intai,birth,shusshin,heya]
        ))
    except AttributeError as e:
        print(e)
        print(f"Rikishi page {id_} is improperly formatted ")
        return None
# END OF idToRikishi
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def main():
    write_opt = 'w'
    file_path = ''
    if len(sys.argv) > 1 and sys.argv[1] == 'a':
        write_opt = 'a'
    if len(sys.argv) > 2:
        file_path = sys.argv[2]

    downloadProfiles(write_opt, file_path)

if __name__ == "__main__":
    main()