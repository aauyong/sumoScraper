import pandas   as pd

from pathlib import Path

DIV_MAP = {
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

directory = r'.\matchupData'
data = Path(directory)
mstrdf = pd.DataFrame()
if not Path(r".\fullMatchups.csv").exists():
    for idx, file in enumerate(data.iterdir()):
        print(f"{idx}: {file.name}")
        curr_mu = pd.read_csv(file, dtype = {'BASHO':str,
                                            'DAY':int,
                                            'OPP':int,
                                            'RESULT':str,
                                            'KIMARITE':str})
        curr_mu['ID'] = file.name.split(".csv")[0]
        mstrdf = pd.concat([curr_mu, mstrdf])

    mstrdf['MU_ID'] = mstrdf['ID'].astype(str) + '.' \
        + mstrdf['OPP'].astype(str)+ '.' \
        + mstrdf['BASHO']+ '.' \
        + mstrdf['DAY'].astype(str)
else:
    mstrdf = pd.read_csv(r".\fullMatchups.csv")

iddf = pd.read_csv(r".\fullResults.csv")

def foo(df:pd.DataFrame, iddf:pd.DataFrame, id_col:str, rank_col:str):
    """Using a {id_col} key, join dataframes on the key column and
    the pull the RANK_NAME column from the {iddf}. Apply the DIV_MAP
    to the rank_name column and store it in the {rank_col} column"""

    df[id_col] = df['ID'].astype(str) + '.' + df['BASHO'].astype(str)
    df = df.set_index(id_col)
    iddf = iddf.set_index(id_col)

    df = df.join(iddf['RANK_NAME'])
    df[rank_col] = df['RANK_NAME'].apply(lambda x : DIV_MAP.get(x, 7))
    df.drop(columns=['RANK_NAME'],inplace=True)
    df.reset_index(drop=True, inplace=True)

foo(mstrdf, iddf, 'RESULT_ID', 'DIVID')
foo(mstrdf, iddf, 'OPP_RESULT_ID', 'DIVOPP')

mstrdf['DIVISION'] = mstrdf[['DIVID', 'DIVOPP']].max(axis=1)
mstrdf.drop(columns=['DIVID', 'DIVOPP'],inplace=True)
mstrdf.sort_values(by=['ID','BASHO','DAY'], inplace=True)

mstrdf.to_csv(r".\fullMatchups.csv", index=False)
