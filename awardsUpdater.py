from bs4 import BeautifulSoup as bs
from bs4 import element

from typing import Tuple, Union

import helpers
import pandas as pd
import re


AWARD_URL = r'https://sumo.or.jp/EnHonbashoMain/champions/'
SAVE_LOCATION = r'C:\Users\blarg\Documents\SQL Server Management Studio\SumoScripts\{}'

def scrapeAwardCell(cell_src: element.Tag) -> Tuple[Union[int, None], Union[str, None]]:
    """***************************************************************************

    Scrape the award cell from the {page_src} to get the id number of and type
    of winner. Ex. If a

    ### Parameters ###
    * cell_src : the page source of a cell to parse through and scrape data from.
                Must contain a h3 with the name of the award, and a table

    ### Return ###
    * (Id, Type of Winner String). If either can't be found, then None is returned
    ***************************************************************************"""
    title = None
    id_ = None
    try:
        title = cell_src.select_one("h3.mdTtl6.type2").text
        title = extractTitle(title)
    except AttributeError:
        pass


    try:
        id_ = cell_src.select_one(".mdTable3.type2 > tbody > tr > th > a")
        id_ = extractJsaId(id_['href'])
    except AttributeError:
        pass

    return (id_, title)


# END OF scrapeAwardCell
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def extractTitle(title: str) -> Union[str, None]:
    """***************************************************************************

    Extract the division or award type from the title string

    ### Parameters ###
    * title : String containing division or type of award

    ### Return ###
    * Abbreviated form of award
    ***************************************************************************"""
    awrdLoc = title.find("(")
    if (awrdLoc > 0):
        return title[:awrdLoc]
    else:
        return title.split(' ')[0]
# END OF extractTitle
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def extractJsaId(url: str) -> Union[int, None]:
    """***************************************************************************

    Extract a url from a jsa sumo url that points to a profile for a wrestler

    ### Parameters ###
    * url : A JSA formatted url that points to the profile of a sumo wrestler

    ### Return ###
    * int of the JSA id that the url references, None if id cannot be found
    ***************************************************************************"""
    patt = r".*/(\d+)/"
    m = re.match(patt, url)
    if not m or len(m.groups()) == 0:
        return None

    return int(m.groups()[0])
# END OF extractJsaId
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def downloadAwards(page_src: str) -> pd.DataFrame:
    """***************************************************************************

    Driver to download the awards for the most recent basho. Returns the results
    as a dataframe, with each point being a jsa_id and the resulting award/championship
    that the wrestler has gotten

    ### Parameters ###
    * driver : Selenium webdriver to scrape page source for

    ### Return ###
    * A formatted dataframe
    ***************************************************************************"""

    soup = bs(page_src, 'html.parser')
    winners = soup.select_one("div.mdSection1:nth-child(1)")
    awards = soup.select_one("#sansho")

    winners_results = list()
    for winner in winners.select(".mdSection1"):
        winners_results.append(scrapeAwardCell(winner))
    win_df = pd.DataFrame(data=winners_results, columns=["jsa_id", "division"])
    win_df['division'] = win_df['division'].apply(lambda x : helpers.DIV_MAP[x.lower()])

    awrd_results = list()
    for awrd in awards.select(".mdSection1"):
        awrd_results.append(scrapeAwardCell(awrd))
    awrd_df = pd.DataFrame(data=awrd_results, columns=['jsa_id', 'award'])

    return win_df, awrd_df
# END OF downloadAwards
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def main():
    with helpers.getHeadlessDriver(AWARD_URL) as driver:
        page_src = driver.page_source

    win_data, awrd_data = downloadAwards(page_src)
    win_data.to_csv(SAVE_LOCATION.format("winners.csv"), index=False)
    awrd_data.to_csv(SAVE_LOCATION.format("awards.csv"), index=False)

if __name__ == "__main__":
    main()
