import datetime as dt
import pandas as pd
import sys

from helpers import *
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from bs4 import BeautifulSoup as bs, Tag


BANZUKE_URL = "https://sumo.or.jp/EnHonbashoBanzuke/index/"
PROFILE_URL = "https://sumo.or.jp/EnSumoDataRikishi/profile/{}/"
SAVE_DESTINATION = r"C:\Users\blarg\Documents\SQL Server Management Studio\SumoScripts\newBasho.csv"
DIV_MAP = {"M": 1, "J": 2, "Ms": 3, "Sd": 4, "Jd": 5, "Jk": 6}

BANZUKE_DICT = {
    "shikona": None, "jsa_id": None, "rank_name": None, "pos": None, "side": None, "other": None, "division": None
}

PROFILE_DICT = {
    "hatsu": None,
    "intai": None,
    "full_shikona": None,
    "heya": None,
    "name": None,
    "shusshin": None,
    "height": None,
    "weight": None,
    "birth_date": None,
    "is_new": None
}

PROFILE_HDRS = list(PROFILE_DICT.keys())

SYS_ARGS = {
    "write_option": 'w'
}

TEMP_BANZUKE = r".\tempBanzData.csv"
TEMP_PROFILE = r".\tempProfileData.csv"

def downloadBanzuke(write_option: str = 'w') -> pd.DataFrame:
    """***************************************************************************

    Download the banzuke ranks and rikishi from teh official sumo website.

    ### Parameters ###
    *

    ### Return ###
    *
    ***************************************************************************"""
    filtered_div_map = DIV_MAP.copy()
    if write_option == 'a':
        append_df = pd.read_csv(TEMP_BANZUKE)
        parsed_divisions = append_df['division'].unique()
        for key, val in DIV_MAP.items():
            if val in parsed_divisions:
                filtered_div_map.pop(key)

    data = list()
    try:
        with getHeadlessDriver(BANZUKE_URL) as banzuke_driver:
            for key in filtered_div_map.keys():
                print(f"Parsing the {key} page")
                data.extend(scrapeBanzuke(banzuke_driver, key))
    except Exception as e:
        print(e)
    finally:
        if len(data) == 0:
            return pd.read_csv(TEMP_BANZUKE)

        df = pd.DataFrame(data=data)
        df.drop_duplicates(inplace=True)
        df[PROFILE_HDRS] = None
        df.to_csv(TEMP_BANZUKE, index=False,
                  mode=write_option, header=(write_option != 'a'))
    if write_option == 'a':
        df = pd.concat([append_df, df])
    return df
# END OF downloadBanzuke
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def scrapeCell(cell: Tag, full_rank: str, division: str, side: str, dummy_pos: int) -> dict:
    """***************************************************************************

    Parse a BS tag cell of the banzuke for shikona information and the JSA sumo id
    attached to the wrestler

    ### Parameters ###
    * cell : bs4 tag containing the inforamtion

    ### Exceptions ###
    * Catches AttributeError -> returns None

    ### Return ###
    * dict mapping shikona and sumo_id respectively
    ***************************************************************************"""
    try:
        rikishi_data = cell.find("dl")

        shikona = rikishi_data.find("dt").text
        if (len(shikona) == 0):
            return None
        jsa_id = rikishi_data.find("a")["href"]
        jsa_id = jsa_id[jsa_id.rfind("/") + 1:]

        if full_rank[0] == "#":
            rank = division
            pos = full_rank[1:]
        else:
            rank = full_rank[0]
            pos = dummy_pos

        other = None

        return dict(zip(
            BANZUKE_DICT.keys(), [shikona, jsa_id, rank,
                                  pos, side, other, DIV_MAP[division]]
        ))

    except AttributeError as e:
        print("Passed tag did not contain appropriately formatted information")
        print(e)
        return None
# END OF parseCell
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def scrapeBanzuke(driver: webdriver, division: str) -> list:
    """***************************************************************************

    Parses the official Sumo webpage banzuke page, and returns the information
    in the form of a list of dictionaries. Each list entry represents a row
    with a mapping in each.

    ### Parameters ###
    * division : Character string for division

    ### Return ###
    * Dict
    ***************************************************************************"""
    driver_waiter = WebDriverWait(driver, timeout=30)
    selector = driver_waiter.until(
        lambda x: Select(x.find_element("id", "kaku_select"))
    )

    division_title = driver_waiter.until(
        lambda x: x.find_element("css selector", ".dayNum")
    )
    selector.select_by_value(value=str(DIV_MAP[division]))

    try:
        if division != 'M':
            driver_waiter.until(ec.element_to_be_selected(division_title))
    except StaleElementReferenceException:
        pass

    soup = bs(driver.page_source, "html.parser")
    rikishi_rows = soup.select(".bTnone")
    try:
        next_page = None
        try:
            next_page = driver_waiter.until(
                lambda x: x.find_element("css selector", ".page_next")
            )
        except TimeoutException as e:
            pass

        while (next_page != None):
            try:
                next_page_link = WebDriverWait(next_page, timeout=30).until(
                    lambda x: x.find_element("link text", ">")
                )
            except TimeoutException:  # No Element
                break

            next_page_link.click()
            driver_waiter.until(
                ec.staleness_of(next_page_link)
            )

            soup = bs(driver.page_source, "html.parser")
            rikishi_rows.extend(soup.select(".bTnone"))
            next_page = driver_waiter.until(
                lambda x: x.find_element("css selector", ".page_next")
            )
    except NoSuchElementException:
        pass

    page_data = list()
    rank_map = set()
    prev_rank = ""
    pos = 1
    for row in rikishi_rows:
        try:
            rank = row.select(".rank")[0].text
            if (rank == prev_rank):
                pos += 1
            else:
                pos = 1
            prev_rank = rank

            east = row.select(".east")
            if (east != None):
                east_data = scrapeCell(east[0], rank, division, "e", pos)
                if (east_data):
                    east_rank = f"{east_data['rank_name']}{east_data['pos']}{east_data['side']}"
                    if east_rank in rank_map:
                        east_data['other'] = "TD"
                    rank_map.add(east_rank)
                    page_data.append(east_data)

            west = row.select(".west")
            if (west != None):
                west_data = scrapeCell(west[0], rank, division, 'w', pos)
                if (west_data):
                    west_rank = f"{west_data['rank_name']}{west_data['pos']}{west_data['side']}"
                    if west_rank in rank_map:
                        west_data['other'] = "TD"
                    rank_map.add(west_rank)
                    page_data.append(west_data)

        except Exception as e:
            print(f"error {e}")
            continue
    return page_data
# END OF parseBanzuke
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def downloadProfiles(write_option: str, toDo_ids: set) -> pd.DataFrame:
    """***************************************************************************



    ### Parameters ###
    *

    ### Return ###
    *
    ***************************************************************************"""
    finished_ids = []
    if write_option == 'a':
        append_df = pd.read_csv(TEMP_PROFILE)
        finished_ids = append_df.dropna(subset='full_shikona')[
            'jsa_id'].unique()

    for id_ in finished_ids:
        toDo_ids.remove(id_)
    try:
        with getHeadlessDriver(None) as driver:
            profile_data = parseProfiles(driver, toDo_ids)
    except Exception as e:
        print(e)
    finally:
        prof_df = pd.DataFrame(data=profile_data)
        prof_df.to_csv(TEMP_PROFILE, index=False,
                       mode=write_option, header=(write_option != 'a'))

    if write_option == 'a':
        prof_df = pd.concat([append_df, prof_df])
    return prof_df
# END OF sca
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def getProfileData(page_source: str, jsa_id: int) -> dict:
    """***************************************************************************
    __summary__:
    Parse the rikishi profile of a given id number. Return information in the form
    of a dictionary

    ### Parameters ###
    * jsa_id : ID number to profile

    ### Returns ###
    * dict { "height": {@code height}, "weight": {@code weight} }
    ***************************************************************************"""
    try:
        soup = bs(page_source, "html.parser")
        profile_tbl = soup.find("table", class_="mdTable2")
    except AttributeError:
        print(f"Couldn't find table for {jsa_id}")
        return PROFILE_DICT

    def findNextOfElemWString(elem: str, string_: str) -> str:
        """Temporary Helper for parsing the profile table

        Args:
            elem (str): _description_
            string_ (str): _description_

        Returns:
            str: _description_
        """
        text = None
        try:
            text = profile_tbl.find(
                elem, string=string_).find_next_sibling("td").text
            text = text.lstrip().rstrip()
        except AttributeError as e:
            print(f"{jsa_id} has no {string_}")
            return None

        return text

    height = findNextOfElemWString("th", "Height")
    if height != None:
        height = height[:height.find("cm")]

    weight = findNextOfElemWString("th", "Weight")
    if weight != None:
        weight = weight[:weight.find("kg")]

    birth_date = findNextOfElemWString("th", "Date of Birth")

    heya = findNextOfElemWString("th", "Heya")

    name = findNextOfElemWString("th", "Name")
    if name != None:
        name = ' '.join(name.split(' ')[::-1])  # flip last and first name

    place_of_birth = findNextOfElemWString("th", "Place of Birth")

    hatsu = ""
    try:
        hatsu = soup.select_one(".mdRankBox3 > .mdBox5 > dl").find("dd").text
        tmp_dt = dt.datetime.strptime(hatsu, "%B, %Y")
        hatsu = f"{tmp_dt.year}.{str(tmp_dt.month).zfill(2)}"
    except AttributeError:
        print(f"{jsa_id}: No Hatsu Date")

    intai = findNextOfElemWString("th", "Retire")
    if intai != None:
        tmp_dt = dt.datetime.strptime(intai, "%B, %Y")
        intai = f"{tmp_dt.year}.{str(tmp_dt.month).zfill(2)}"

    full_shikona = profile_tbl.find(
        "td", class_="fntXL").text.lstrip().rstrip()

    is_new = False
    try:
        recent_record = soup.select("tbody > .bBnone.name:not(.hoshitoriAll)")
        is_new = len(recent_record) <= 1
    except AttributeError as e:
        print(f"can't find career record, assuming not new")
    is_new = int(is_new)

    return {
        "hatsu": hatsu,
        "intai": intai,
        "full_shikona": full_shikona,
        "heya": heya,
        "name": name,
        "shusshin": place_of_birth,
        "height": height,
        "weight": weight,
        "birth_date": birth_date,
        "is_new": is_new
    }
# END OF getProfileData
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def parseProfiles(driver: webdriver.Firefox, jsa_ids: list) -> list:
    """***************************************************************************

    Uses a given driver to parse all the profile pages listed in the jsa_ids list.
    Any errors or denied ranges are writtten into the error_log.txt

    ### Parameters ###
    * driver : Firefox Webdriver used to parse pages
    * jsa_id : jsa Id number used to format url and download data

    ### Return ###
    * List of all the profile data
    ***************************************************************************"""
    errors = list()
    data = list()
    try:
        for idx, id in enumerate(jsa_ids):
            print(f"{id}: Parsing Profile {idx+1}/{len(jsa_ids)}")

            MAX_ERROR = 10
            error_cnt = 0
            driver.get(PROFILE_URL.format(id))
            for _ in range(MAX_ERROR):
                if (ec.url_matches(PROFILE_URL.format(id))(driver)):
                    break
                else:
                    print(f"{driver.current_url} for {id}, retrying")
                    driver.get(PROFILE_URL.format(id))
                    error_cnt += 1

            if error_cnt >= 9:
                errors.append(f"{id}\n")
            else:
                WebDriverWait(driver, timeout=30).until(
                    ec.presence_of_element_located(("css selector", ".mdTable2")))
                d = getProfileData(driver.page_source, id)
                data.append(d)

    except Exception as e:
        print(e)
    finally:
        with open("error_log.txt", 'w') as f:
            f.writelines(errors)
        return data
# END OF parseProfiles
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def consolidateWithSumoDB(df: pd.DataFrame) -> pd.DataFrame:
    """***************************************************************************

    Consolidate profiles pulled from the Sumo website with the sumodb. In
    particular pulling down the db ids. Uses ranks to find

    ### Parameters ###
    * df : Dataframe containing jsa website data

    ### Return ###
    * Dataframe with ID column
    ***************************************************************************"""
    soup = None
    with getHeadlessDriver(r"http://sumodb.sumogames.de/Banzuke.aspx") as driver:
        WebDriverWait(driver, timeout=30).until(
            ec.url_matches(r"http://sumodb.sumogames.de/Banzuke.aspx"))
        soup = bs(driver.page_source, 'html.parser')

    df['id'] = None
    for i in range(len(df)):
        rank = df.loc[i]['rank_name']
        pos = 0
        if rank not in ['Y', 'O', 'S', 'K']:
            rank += str(df.loc[i]['pos'])
        else:
            pos = df.loc[i]['pos'] - 1

        elem = soup.find_all("td", string=rank, class_='short_rank')[pos]
        wrestler = None
        if df.loc[i]['side'] == 'e':
            wrestler = elem.find_previous_sibling('td')
        else:
            wrestler = elem.find_next_sibling('td')

        id_ = wrestler.find('a')['href']
        id_ = id_[id_.find("r=") + 2:]
        df.loc[i, 'id'] = id_
    return df
# END OF consolidateWithSumoDB
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def readErrors() -> None:
    """***************************************************************************



    ### Parameters ###
    *

    ### Return ###
    *
    ***************************************************************************"""
    error_ids = set()
    with open("error_log.txt", 'r') as f:
        for line in f.readlines():
            error_ids.add(line.lstrip().rstrip())

    data = list()
    with getHeadlessDriver() as driver:
        data = parseProfiles(driver, error_ids)

    if len(data) <= 0:
        return -1

    err_data = pd.DataFrame(data=data)
    mstrdf = pd.read_csv(SAVE_DESTINATION)
    print()
# END OF readErrors
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'a':
        SYS_ARGS['write_option'] = sys.argv[1]
        try:
            open(TEMP_PROFILE, 'r')
        except FileNotFoundError as e:
            print(e)
            return 1
    if len(sys.argv) > 1 and sys.argv[1] == 'read_errors':
        readErrors()
        return 0

    banz_df = downloadBanzuke(SYS_ARGS['write_option'])
    print("PARSING PROFILE DATA")
    prof_df = downloadProfiles(
        SYS_ARGS['write_option'], set(banz_df['jsa_id'].unique()))

    mstrdf = banz_df.set_index('jsa_id')
    mstrdf.update(prof_df.set_index('jsa_id'))
    mstrdf = mstrdf.reset_index()

    mstrdf["birth_date"] = pd.to_datetime(mstrdf["birth_date"])
    now = dt.datetime.now()
    month = now.month
    if month % 2 == 0:
        month += 1

    mstrdf['year'] = str(now.year)
    mstrdf['basho_num'] = month
    mstrdf['basho'] = f"{now.year}.{str(month).zfill(2)}"

    consolidateWithSumoDB(mstrdf)

    mstrdf = mstrdf.convert_dtypes()
    mstrdf.to_csv(
        SAVE_DESTINATION,
        index=False
    )
    os.remove(TEMP_BANZUKE)
    os.remove(TEMP_PROFILE)
    return 0

if __name__ == "__main__":
    main()
