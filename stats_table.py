from bs4 import BeautifulSoup
import requests
import pandas as pd


def get_combined_stats_table(year):
    df_basic = get_single_stats_table(year, "basic")
    df_advanced = get_single_stats_table(year, "advanced")
    
    df_combined = pd.concat([df_basic, df_advanced], axis=1)
    df_combined = df_combined.loc[:,~df_combined.columns.duplicated()]
    
    return df_combined


def get_single_stats_table(year, typ):
    base_url = "https://www.sports-reference.com/cbb/seasons/YYYY-SSSS.html"
    
    if typ == "basic":
        stats_str = "school-stats"
        table_id = "basic_school_stats"
    elif typ == "advanced":
        stats_str = "advanced-school-stats"
        table_id = "adv_school_stats"
    
    url = base_url.replace("YYYY", str(year))
    url = url.replace("SSSS", stats_str)

    req = requests.get(url)
    soup = BeautifulSoup(req.content, "html.parser")

    table = soup.find("table", {"id": table_id})
    table_str = str(table)
    df = pd.read_html(table_str)[0]
    df = clean_stats_table(df)

    return df


def clean_stats_table(df):
    # Change column names to remove multi-level column index
    new_cols = []

    for col_name in df.columns.values:
        if col_name[0].startswith("Unnamed") or col_name[0] == "Totals" or col_name[0] == "School Advanced":
            cn = col_name[1]
        else:
            cn = "".join([col_name[0], "_", col_name[1]])

        new_cols.append(cn)

    df.columns = new_cols
    
    # Drop spacing columns
    drop_inds = [0] # always drop the "rank" columns, which is just alpha ordering

    for i, col_name in enumerate(df.columns.values):
        if col_name.startswith("Unnamed"):
            drop_inds.append(i)

    df = df.drop(columns=df.columns[drop_inds])
    
    # Set index to school name, drop spacing rows
    df = df.dropna(axis=0) # need to do this first
    df = df.set_index("School")
    df = df.drop(index="School")
    
    # Remove NCAA from tournament team names
    teams = df.index.values

    for i in range(len(teams)):
        if teams[i][-4:] == "NCAA":
            teams[i] = teams[i][:-5]

    df.index = teams
    
    return df