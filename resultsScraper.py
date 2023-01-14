import os
from pathlib import Path
import pandas as pd
import re

from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from helpers import *
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from typing import Union


RIKISHI_URL = 'http://sumodb.sumogames.de/Rikishi.aspx?r={}'

RESULT_HDRS = ["BASHO", "SHIKONA", "NAME", "RANK", "RECORD_STR",
               "W", "L", "A", "AWARD", "HEIGHT", "WEIGHT"]

MAPPING = {
    'img/hoshi_shiro.gif': 'O',
    'img/hoshi_kuro.gif': 'X',
    'img/hoshi_yasumi.gif': '-',
    'img/hoshi_fusenpai.gif': 'A',
    'img/hoshi_fusensho.gif': 'Z',
    "img/hoshi_empty.gif": ' ',
    "img/hoshi_hikiwake.gif": "D"
}

SYS_ARG_DEFAULTS = {
    "write_option": 'w',
    "strt": 1,
    "end": 15000,
    "use_values": r"\ids.txt"
}

SAVE_DIR = r'.\wrestlerData'


def removeAlpha(s: str):
    match = re.match(r"\d*", s)
    return s[match.span()[0]:match.span()[-1]]


def scrapeRecordStr(record_cell: Tag, rank: Union[str, None]) -> Union[str, None]:
    """***************************************************************************

    From teh record cell, parse the win/loss images and produce a string
    representing the record.

    If the rank is in Bg or Mz, then produce a string of all '-'

    Otherwise, return a none

    ### Parameters ###
    * record_cell : Tag representing the cell containing the results of 15 days
                    for the basho
    * rank : string of the record, if in Mz or Bg, then produce a blank

    ### Return ###
    *
    ***************************************************************************"""
    if rank == None:
        return None
    elif rank in ['Bg', 'Mz']:
        record_str = 15 * '-'
    else:
        record_str = ''
        for s in record_cell.find_all("img"):
            record_str += MAPPING[s['src']]
    return record_str


def scrapeRikishi(page_src: str, id_: int, directory: str) -> bool:
    """***************************************************************************

    Scrapes a rikishi page by their identification number and writes it into its
    own CSV file

    ### Parameters ###
    * x : An integer value representing the Id number of a rikishi

    ***************************************************************************"""
    soup = bs(page_src, "html.parser")
    curr_name = ""
    data = []
    try:
        results = soup.find(class_="rikishi").find_all("tr")
        for row in results:
            data_pt = dict(zip(
                RESULT_HDRS, [None for _ in range(len(RESULT_HDRS))]
            ))

            cells = dict(zip(
                ['basho', 'rank', 'record_str', 'record', 'awards', 'bio_data'], row.find_all("td")))
            if len(cells) <= 0:
                shikona = row.find("th")
                if shikona != None:
                    curr_name = shikona.text
                continue

            data_pt["BASHO"] = cells['basho'].text
            if cells['rank'].text != '??':
                data_pt["RANK"] = cells['rank'].text

            data_pt["SHIKONA"] = curr_name.split(" ")[0]
            data_pt["NAME"] = curr_name

            # Record split into W, L, A
            record = list(cells['record'].text.split('-'))
            if not record:
                record = [None, None, None]
            else:
                record = [removeAlpha(s) for s in record]

            while len(record) < 3:
                record.append('0')
            # data_pt['W'] = record[0]
            # data_pt['L'] = record[1]
            # data_pt['A'] = record[2]
            (data_pt['W'], data_pt['L'], data_pt['A']) = tuple(record)[:3]

            # Record
            try:
                data_pt['RECORD_STR']= scrapeRecordStr(cells['record_str'], data_pt['RANK'])
            except AttributeError:
                print(f"{id_} has weirdly formatted record_str")

            # Awards
            try:
                if data_pt['RANK']:
                    if cells['awards'].text == '\xa0':
                        data_pt['AWARD'] = ' '
                    else:
                        data_pt['AWARD'] = cells['awards'].text
            except AttributeError:
                print(f"{id_} is missing an Award cell")
            # height weight
            try:
                hghtwght = cells['bio_data'].text
                hghtwght = hghtwght.replace(" cm", ',')
                hghtwght = hghtwght.replace(" kg", '')
                hghtwght = hghtwght.split(',')
                if len(hghtwght) == 2:
                    data_pt['HEIGHT'] = hghtwght[0]
                    data_pt['WEIGHT'] = hghtwght[1]
            except AttributeError:
                print(f"{id_} is missing a heightweight cell")

            data.append(data_pt)
        # end of FOR

        df = pd.DataFrame(data=data, columns=RESULT_HDRS)
        df.to_csv(f"{directory}/{id_}.csv",
                  index=False, mode='x', na_rep='DNE')
    except AttributeError as e:
        print(f"Rikishi page {id_} is improperly formatted or does not exist ")
        print(f"error: {e}")
        return False

    return True
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~END OF scrapeRikishi~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def idCheck() -> list:

    """***************************************************************************

    Checks the ids that need to be scraped. First checks the {SAVE_DIR} folder
    for what has already been accomplished, then compares to the id.csv
    file for what needs to be finished

    ### Parameters ###
    * :

    ### Return ###
    * List of ids to do
    ***************************************************************************"""
    p = Path(SAVE_DIR)
    df = pd.read_csv("id.csv")

    total_ids = set(df['id'].unique())
    if p.exists():
        done_ids = set()
        for f in p.iterdir():
            done_ids.add( int(f.name.replace(".csv", "")) )
        return total_ids.difference(done_ids)
    else:
        return total_ids
# END OF idCheck
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def runScraper():
    running = True
    while (running):
        ids = idCheck()
        with getHeadlessDriver() as driver:
            waiter = WebDriverWait(driver, timeout=20)
            fail_cnt = 0
            succ_cnt = 0
            for idx, id_ in enumerate(ids):
                print(f"{idx+1}/{len(ids)}")
                if fail_cnt >= 10:
                    print(f"too much failure, qutting")
                    return -1

                if os.path.isfile(SAVE_DIR+f"\\{id_}.csv"):
                    print(f"{id_} exists, continuing")
                    continue

                print(f"scraping {id_}")
                url = RIKISHI_URL.format(id_)
                driver.get(url)
                try:
                    waiter.until(ec.all_of(
                        ec.url_to_be(url)
                        , ec.presence_of_element_located(
                            ("css selector", ".rikishi"))
                    ))
                except TimeoutException:
                    print(f"Timed Out {id_}")
                    fail_cnt += 1
                    continue

                if (not scrapeRikishi(driver.page_source, id_, SAVE_DIR)):
                    print(f"{id_} failed")
                    fail_cnt += 1
                else:
                    print(f"done {id_}")
                    fail_cnt = 0
                    succ_cnt += 1

        print(f"Completed {succ_cnt} of {len(ids)}")
        print(f"{len(ids) - succ_cnt} remaining")
        usr_inp = ''
        while (usr_inp not in ['y', 'n']):
            usr_inp = input("Retry? Yes(y), No(n) ")
        running = usr_inp == 'y'
    print("Closing")

def main():
    runScraper()
    return


if __name__ == "__main__":
    main()
