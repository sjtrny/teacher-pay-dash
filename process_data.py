import warnings
from multiprocessing import Pool, cpu_count, get_context

warnings.simplefilter("ignore", UserWarning)

import numpy as np
import pandas as pd
from binsmooth import BinSmooth

column_mapping_2021 = {
    "4-digit level OCCP Occupation": "OCCP4D",
    "INCP Total Personal Income (weekly)": "INCP",
    "AGE10P Age in Ten Year Groups": "AGE10P",
    "STATE (POW)": "STATE",
    "Unnamed: 4": "COUNT",
}

column_mapping_2016 = {
    "OCCP - 4 Digit Level": "OCCP4D",
    "INCP Total Personal Income (weekly)": "INCP",
    "AGE10P - Age in Ten Year Groups": "AGE10P",
    "STATE (POW)": "STATE",
    "Unnamed: 4": "COUNT",
}

column_mapping_2011 = {
    "OCCP Occupation": "OCCP4D",
    "INCP Total Personal Income (weekly)": "INCP",
    "AGE10P  Age in Ten Year Groups": "AGE10P",
    "Main Statistical Area Structure (Main ASGS) (POW)": "STATE",
    "Unnamed: 4": "COUNT",
}

column_mapping_2006 = {
    "OCC06P Occupation 06 (ANZSCO)": "OCCP4D",
    "INCP Individual Income (gross weekly)": "INCP",
    "AGEP Age (10 Year Groups)": "AGE10P",
    "Main ASGC": "STATE",
    "Unnamed: 4": "COUNT",
}

incp_low_mapping_2021 = {
    "$400-$499 ($20,800-$25,999)": 400,
    "$500-$649 ($26,000-$33,799)": 500,
    "$650-$799 ($33,800-$41,599)": 600,
    "$800-$999 ($41,600-$51,999)": 800,
    "$1,000-$1,249 ($52,000-$64,999)": 1000,
    "$1,250-$1,499 ($65,000-$77,999)": 1250,
    "$1,500-$1,749 ($78,000-$90,999)": 1500,
    "$1,750-$1,999 ($91,000-$103,999)": 1750,
    "$2,000-$2,999 ($104,000-$155,999)": 2000,
    "$3,000-$3,499 ($156,000-$181,999)": 3000,
    "$3,500 or more ($182,000 or more)": 3500,
}

incp_high_mapping_2021 = {
    "$400-$499 ($20,800-$25,999)": 499,
    "$500-$649 ($26,000-$33,799)": 649,
    "$650-$799 ($33,800-$41,599)": 799,
    "$800-$999 ($41,600-$51,999)": 999,
    "$1,000-$1,249 ($52,000-$64,999)": 1249,
    "$1,250-$1,499 ($65,000-$77,999)": 1499,
    "$1,500-$1,749 ($78,000-$90,999)": 1749,
    "$1,750-$1,999 ($91,000-$103,999)": 1999,
    "$2,000-$2,999 ($104,000-$155,999)": 2999,
    "$3,000-$3,499 ($156,000-$181,999)": 3499,
    "$3,500 or more ($182,000 or more)": 7000,
}

incp_low_mapping_2016 = {
    "$400-$499 ($20,800-$25,999)": 400,
    "$500-$649 ($26,000-$33,799)": 500,
    "$650-$799 ($33,800-$41,599)": 600,
    "$800-$999 ($41,600-$51,999)": 800,
    "$1,000-$1,249 ($52,000-$64,999)": 1000,
    "$1,250-$1,499 ($65,000-$77,999)": 1250,
    "$1,500-$1,749 ($78,000-$90,999)": 1500,
    "$1,750-$1,999 ($91,000-$103,999)": 1750,
    "$2,000-$2,999 ($104,000-$155,999)": 2000,
    "$3,000 or more ($156,000 or more)": 3000,
}

incp_high_mapping_2016 = {
    "$400-$499 ($20,800-$25,999)": 499,
    "$500-$649 ($26,000-$33,799)": 649,
    "$650-$799 ($33,800-$41,599)": 799,
    "$800-$999 ($41,600-$51,999)": 999,
    "$1,000-$1,249 ($52,000-$64,999)": 1249,
    "$1,250-$1,499 ($65,000-$77,999)": 1499,
    "$1,500-$1,749 ($78,000-$90,999)": 1749,
    "$1,750-$1,999 ($91,000-$103,999)": 1999,
    "$2,000-$2,999 ($104,000-$155,999)": 2999,
    "$3,000 or more ($156,000 or more)": 7000,
}

incp_low_mapping_2011 = {
    "$400-$599 ($20,800-$31,199)": 400,
    "$600-$799 ($31,200-$41,599)": 600,
    "$800-$999 ($41,600-$51,999)": 800,
    "$1,000-$1,249 ($52,000-$64,999)": 1000,
    "$1,250-$1,499 ($65,000-$77,999)": 1250,
    "$1,500-$1,999 ($78,000-$103,999)": 1500,
    "$2,000 or more ($104,000 or more)": 2000,
}

incp_high_mapping_2011 = {
    "$400-$599 ($20,800-$31,199)": 599,
    "$600-$799 ($31,200-$41,599)": 799,
    "$800-$999 ($41,600-$51,999)": 999,
    "$1,000-$1,249 ($52,000-$64,999)": 1249,
    "$1,250-$1,499 ($65,000-$77,999)": 1499,
    "$1,500-$1,999 ($78,000-$103,999)": 1999,
    "$2,000 or more ($104,000 or more)": 7000,
}

incp_low_mapping_2006 = {
    "$400-$599": 400,
    "$600-$799": 600,
    "$800-$999": 800,
    "$1,000-$1,299": 1000,
    "$1,300-$1,599": 1300,
    "$1,600-$1,999": 1600,
    "$2,000 or more": 2000,
}

incp_high_mapping_2006 = {
    "$400-$599": 599,
    "$600-$799": 799,
    "$800-$999": 999,
    "$1,000-$1,299": 1299,
    "$1,300-$1,599": 1599,
    "$1,600-$1,999": 1999,
    "$2,000 or more": 7000,
}


def process_census_data(filepath, column_mapping, incp_low_mapping, incp_high_mapping):
    data = pd.read_csv(
        filepath,
        index_col=False,
        usecols=column_mapping.keys(),
        skiprows=10,
        skipfooter=8,
        engine="python",
    )

    data = data.rename(columns=column_mapping)

    data = data.fillna(method="ffill")

    data = data[
        ~data["OCCP4D"].isin(
            ["Inadequately described", "Not stated", "Not applicable", "Total"]
        )
    ]
    data = data[~data["AGE10P"].isin(["Total"])]

    data["INCP_LOW"] = data["INCP"].apply(lambda x: incp_low_mapping[x])
    data["INCP_HIGH"] = data["INCP"].apply(lambda x: incp_high_mapping[x])

    return data


def task(index, row):

    year = row["YEAR"]
    occ = row["OCCP4D"]
    age_group = row["AGE10P"]
    state = row["STATE"]

    subset = data.query(
        f"OCCP4D == '{occ}' and AGE10P == '{age_group}' and STATE == '{state}' and YEAR == {year}"
    )
    subset = subset.sort_values("INCP_HIGH", ascending=True)

    # If the subset has no observations then fill with 0
    if subset["COUNT"].sum() > 0:
        edges = subset["INCP_HIGH"].values
        counts = subset["COUNT"].values

        # Collapse zeros
        idx = counts != 0
        edges = edges[idx]
        counts = counts[idx]
        edges = np.concatenate(([0], edges))
        counts = np.concatenate(([0], counts))

        bs = BinSmooth()
        bs.fit(
            edges,
            counts,
            includes_tail=True,
        )

        pcntile_vals = bs.inv_cdf(pcntile_range)
    else:
        pcntile_vals = np.full(pcntile_range.shape, 0)

    result = pd.concat(
        [
            pd.Series((pcntile_range.squeeze() * 100).astype(int), name="PERCENTILE"),
            pd.Series(pcntile_vals.squeeze().round(4), name="PERCENTILE_VALUE"),
        ],
        axis=1,
    )

    result["YEAR"] = year
    result["OCCP4D"] = occ
    result["AGE10P"] = age_group
    result["STATE"] = state

    return result


if __name__ == "__main__":

    data_2021 = process_census_data(
        "data/teacher_pay_2021.csv",
        column_mapping_2021,
        incp_low_mapping_2021,
        incp_high_mapping_2021,
    )
    data_2021["YEAR"] = 2021

    data_2016 = process_census_data(
        "data/teacher_pay_2016.csv",
        column_mapping_2016,
        incp_low_mapping_2016,
        incp_high_mapping_2016,
    )
    data_2016["YEAR"] = 2016

    data_2011 = process_census_data(
        "data/teacher_pay_2011.csv",
        column_mapping_2011,
        incp_low_mapping_2011,
        incp_high_mapping_2011,
    )
    data_2011["YEAR"] = 2011
    #
    data_2006 = process_census_data(
        "data/teacher_pay_2006.csv",
        column_mapping_2006,
        incp_low_mapping_2006,
        incp_high_mapping_2006,
    )
    data_2006["YEAR"] = 2006

    data = pd.concat([data_2021, data_2016, data_2011, data_2006], axis=0)

    combinations = data[["OCCP4D", "AGE10P", "STATE", "YEAR"]].drop_duplicates()

    pcntile_range = np.arange(0, 101, 10).reshape(-1, 1) / 100

    dataframe_list = []
    n_cpu = cpu_count()

    with get_context("fork").Pool(n_cpu) as p:
        dataframe_list = p.starmap(task, combinations.iloc[:, :].iterrows())

    full_result = pd.concat(dataframe_list, axis=0)
    full_result.to_csv("data/percentiles.csv", index=False)
