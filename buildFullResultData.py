import pandas   as pd
import re
import sys

from pathlib import Path

FOLDER = 'wrestlerData'

def splitRank(s:str) -> list:
    if type(s) != type(str()):
        return [None, None, None, None]

    result = re.match(r"(\D*)(\d*)([e|w]*)(\D*)", s)
    groups = [x if len(x) > 0 else ' ' for x in result.groups()]
    while len(groups) < 4:
        groups.append(' ')
    return tuple(groups)

def toInt(s:str):
    if not s:
        return None
    elif s == ' ':
        return 0
    else:
        return int(s)

def division(rank_name:str):
    d = {
        'Y':1
        ,'S':1
        ,'O':1
        ,'K':1
        ,'M':1
        ,'J':2
        ,'Ms':3
        ,'Sd':4
        ,'Jd':5
        ,'Jk':6
    }
    return d.get(rank_name, 7)

def basho_config(basho:str):
    x = basho.split('.')
    return f"{x[0]}.{x[1].zfill(2)}"

data = Path(FOLDER)
mstrdf = pd.DataFrame()
progress_bar = [" " for _ in range(100)]
total_size = len(list(data.iterdir()))
for idx, file in enumerate(data.iterdir()):
    progress = int(idx / total_size * 100)
    progress_bar[progress] = ':'
    sys.stdout.write("\r" + "[" + "".join(progress_bar) + "]")
    sys.stdout.flush()
    temp_df = pd.read_csv(file, dtype={'BASHO':str}, na_values='DNE')
    id_ = int( file.name.split(".csv")[0] )
    temp_df['ID'] = id_
    temp_df["HEIGHT"].fillna(method="ffill", inplace=True)
    temp_df["WEIGHT"].fillna(method="ffill", inplace=True)
    temp_df["HEIGHT"].fillna(method="bfill", inplace=True)
    temp_df["WEIGHT"].fillna(method="bfill", inplace=True)
    mstrdf = pd.concat([mstrdf, temp_df])

for i in range(15):
    val = mstrdf['RECORD_STR'].str[i]
    mstrdf[f"DAY{i+1}"] = val
mstrdf = mstrdf.reset_index(drop=True)
mstrdf['BASHO'] = mstrdf['BASHO'].astype(str).apply(basho_config)
mstrdf["RESULT_ID"] = mstrdf["ID"].astype(str) + "." + mstrdf["BASHO"].astype(str)

elems = mstrdf['RANK'].apply(splitRank)
elems = pd.DataFrame(elems.to_list(), columns=['RANK_NAME','POS', 'SIDE', 'OTHER'])
mstrdf = mstrdf.join(elems)

mstrdf['DIVISION'] = mstrdf['RANK_NAME'].apply(division)
mstrdf['SHIKONA'] = mstrdf['SHIKONA'].apply(lambda x : x.replace('#', '') if type(x) == type(str()) else x)
mstrdf['NAME'] = mstrdf['NAME'].apply(lambda x : x.replace('#', '') if type(x) == type(str()) else x)

mstrdf['POS'] = mstrdf['POS'].apply(toInt)
mstrdf["YEAR"] = mstrdf["BASHO"].astype(str).str.split('.').str[0]
mstrdf["BASHO_NUM"] = mstrdf["BASHO"].astype(str).str.split('.').str[1].astype(int)
mstrdf.drop(columns=["RANK", "RECORD_STR"], inplace=True)
mstrdf = mstrdf.convert_dtypes()
mstrdf.sort_values(by='ID', inplace=True)
mstrdf.to_csv("fullResults.csv", index=False)
