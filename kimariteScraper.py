from helpers import *
from bs4 import BeautifulSoup as bs
import pandas as pd

def main():
    with getHeadlessDriver("https://en.wikipedia.org/wiki/Kimarite#Yoritaoshi") as driver:
        soup = bs(driver.page_source, 'html.parser')

    headers = soup.select(".mw-headline")
    data = list()
    curr_type = None
    for h in headers:
        if (h.parent.name == 'h2' or curr_type == None):
            curr_type = h.text.lower().encode('ascii','ignore').rstrip()
            curr_type = str(curr_type, encoding='utf8')
        else:
            s = h.text.lower().encode('ascii','ignore').rstrip()
            data.append((str(s,encoding='utf8'),curr_type))
    df = pd.DataFrame(data = data, columns=['Kimarite', 'Type'])
    df.to_csv("kimarite.csv", index=False)
if __name__ == '__main__':
    main()