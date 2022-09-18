import pandas   as pd

from pathlib import Path

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
iddf = iddf.set_index("RESULT_ID")
mstrdf['RESULT_ID'] = mstrdf['ID'].astype(str) + '.' + mstrdf['BASHO'].astype(str)
mstrdf = mstrdf.set_index("RESULT_ID")

# mstrdf = mstrdf.join(iddf[['SHIKONA', 'NAME', 'RANK_NAME','POS','SIDE']])
mstrdf = mstrdf.join(iddf[['RANK_NAME','POS','SIDE']])
# mstrdf['IDRANK'] = mstrdf['RANK_NAME'] + mstrdf['POS'].convert_dtypes().astype(str) + mstrdf['SIDE']
mstrdf['DIVID'] = mstrdf['RANK_NAME'].apply(division)
mstrdf.drop(columns=['RANK_NAME', 'POS', 'SIDE'],inplace=True)
mstrdf.reset_index(drop=True, inplace=True)

mstrdf['OPP_RESULT_ID'] = mstrdf['OPP'].astype(str) + '.' + mstrdf['BASHO'].astype(str)
mstrdf = mstrdf.set_index("OPP_RESULT_ID")

# mstrdf = mstrdf.join(iddf[['SHIKONA', 'NAME', 'RANK_NAME','POS','SIDE']], rsuffix="_OPP")
mstrdf = mstrdf.join(iddf[['RANK_NAME','POS','SIDE']], rsuffix="_OPP")
# mstrdf['OPPRANK'] = mstrdf['RANK_NAME'] + mstrdf['POS'].convert_dtypes().astype(str) + mstrdf['SIDE']
mstrdf['DIVOPP'] = mstrdf['RANK_NAME'].apply(division)
mstrdf.drop(columns=['RANK_NAME', 'POS', 'SIDE'],inplace=True)
mstrdf.reset_index(drop=True, inplace=True)

mstrdf['DIVISION'] = mstrdf[['DIVID', 'DIVOPP']].max(axis=1)
mstrdf.drop(columns=['DIVID', 'DIVOPP'],inplace=True)
mstrdf.sort_values(by=['ID','BASHO','DAY'], inplace=True)

mstrdf.to_csv(r".\fullMatchups.csv", index=False)
