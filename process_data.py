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
