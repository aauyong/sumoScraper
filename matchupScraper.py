import  pandas  as  pd

from bs4 import BeautifulSoup as bs
from helpers import *
from pathlib import Path
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

MAPPING = {
    'img/hoshi_shiro.gif':'O',
    'img/hoshi_kuro.gif':'X',
    'img/hoshi_yasumi.gif':'-',
    'img/hoshi_fusenpai.gif':'A',
    'img/hoshi_fusensho.gif':'Z',
    "img/hoshi_empty.gif":' ',
    "img/hoshi_hikiwake.gif": "D"
}

MASTER_URL = "http://sumodb.sumogames.de/Rikishi_opp.aspx?r={}"
MU_HDRS = ["BASHO", "DAY", "OPP", "RESULT", "KIMARITE"]

def getMatchup(pg_src:str, id:int, directory:str) -> bool:
    p = Path(f"{directory}/{id}.csv")
    if p.is_file():
        print(f"{id} exists, continuing")
        return False

    soup = bs( pg_src, "html.parser")

    data = dict( zip (MU_HDRS, [ list() for _ in MU_HDRS ]) )
    seen_matchups = set()
    try:
        results = soup.find_all(class_="ro_torikumi")
        for table in results:
            for row in table.find_all("tr"):
                basho = row.find("td").text
                day = row.find(class_="rb_day").text.replace("Day ", "")

                opp = row.find_all(class_="rb_opp")[1].find('a').get('href')
                opp = opp.replace("Rikishi.aspx?r=", "")

                while f"{basho}.{day}.{opp}" in seen_matchups:
                    day = str(int(day) + 1)
                seen_matchups.add(f"{basho}.{day}.{opp}")

                result = row.find(class_='tk_kekka').find("img")
                if result:
                    result = MAPPING[ result['src'] ]

                kimarite = row.find(class_="rb_kim").text

                for i,val in enumerate([basho, day, opp, result, kimarite]):
                    try:
                        val = val.rstrip().lstrip()
                    except AttributeError as e:
                        print(e)
                        print(f"issues with {id} and {MU_HDRS[i]}")
                        val = None
                        pass
                    data[ MU_HDRS[i] ].append( val )
        df = pd.DataFrame(data=data)
        df['DAY'] = df['DAY'].apply(int)
        df['OPP'] = df['OPP'].apply(int)
        df.sort_values(by=['BASHO', 'DAY','OPP'], inplace=True)
        df.to_csv(f"{directory}/{id}.csv", index=False, mode='x')

        return True

    except AttributeError as e:
        print(f"Rikishi page {id} is improperly formatted or does not exist ")
        print(f"error: {e}")
        return False

def main():
    df = pd.read_csv("id.csv")
    todo_ids = set(df['id'].unique())
    finished_ids = Path(r".\matchupData")
    for dir_ in finished_ids.iterdir():
        x = int(dir_.name.replace(".csv",''))
        try:
            todo_ids.remove(x)
        except KeyError:
            pass

    with getHeadlessDriver() as driver:
        waiter = WebDriverWait(driver, timeout=10)
        fail_cnt = 0
        for idx, id_ in enumerate(todo_ids):
            if fail_cnt >= 10:
                print(f"Too many failures, cancelling")
                return -1

            print(f"scraping {id_}, {idx}/{len(todo_ids)}")
            url = MASTER_URL.format(id_)

            driver.get(url)
            try:
                waiter.until(ec.url_to_be(url))
            except TimeoutException:
                print(driver.current_url)
                print(f"Could not get to {url}")
                fail_cnt += 1
                continue

            try:
                waiter.until(ec.presence_of_all_elements_located(("css selector", "#aspnetForm")))
            except TimeoutException:
                print(f"{url} could not load")
                fail_cnt += 1
                continue

            if len(driver.find_elements("css selector", ".ro_torikumi")) == 0:
                print(f"{url} has no table page")
                fail_cnt = 0
                with open(f"matchupData\\{id_}.csv", 'x') as f: f.write(','.join(MU_HDRS))
                continue

            if (not getMatchup(driver.page_source, id_, "matchupData")):
                print(f"{id_} failed")
                fail_cnt += 1
            else:
                print(f"done {id_}")
                fail_cnt = 0

if __name__ == "__main__":
    main()
