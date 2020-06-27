import numpy as np
import pandas as pd

from util import InverseCDFSmoother
from util import process_census_data, column_mapping_2016, column_mapping_2011, column_mapping_2006, \
    incp_low_mapping_2016, incp_high_mapping_2016, incp_low_mapping_2011, \
    incp_high_mapping_2011, incp_low_mapping_2006, incp_high_mapping_2006

from multiprocessing import Pool

data_2016 = process_census_data("data/teacher_pay_2016.csv", column_mapping_2016, incp_low_mapping_2016, incp_high_mapping_2016)
data_2016['YEAR'] = 2016

data_2011 = process_census_data("data/teacher_pay_2011.csv", column_mapping_2011, incp_low_mapping_2011, incp_high_mapping_2011)
data_2011['YEAR'] = 2011

data_2006 = process_census_data("data/teacher_pay_2006.csv", column_mapping_2006, incp_low_mapping_2006, incp_high_mapping_2006)
data_2006['YEAR'] = 2006

data = pd.concat([data_2016, data_2011, data_2006], axis=0)

combinations = data[['OCCP4D', 'AGE10P', 'STATE', 'YEAR']].drop_duplicates()

pcntile_range = np.arange(0, 101, 10).reshape(-1, 1) / 100

dataframe_list = []

def task(index, row):

    year = row['YEAR']
    occ = row['OCCP4D']
    age_group = row['AGE10P']
    state = row['STATE']

    subset = data.query(
        f"OCCP4D == '{occ}' and AGE10P == '{age_group}' and STATE == '{state}' and YEAR == {year}")
    subset = subset.sort_values("INCP_HIGH", ascending=True)

    # If the subset has no observations then fill with 0
    if subset['COUNT'].sum() > 0:
        smoother = InverseCDFSmoother()
        smoother.fit(subset["INCP_HIGH"].values.reshape(-1, 1), subset["COUNT"])

        pcntile_vals = smoother.predict(pcntile_range)
    else:
        pcntile_vals = np.full(pcntile_range.shape, 0)

    result = pd.concat(
        [
            pd.Series((pcntile_range.squeeze() * 100).astype(int), name="PERCENTILE"),
            pd.Series(pcntile_vals.squeeze().round(4), name="PERCENTILE_VALUE"),
        ],
        axis=1
    )

    result['YEAR'] = year
    result['OCCP4D'] = occ
    result['AGE10P'] = age_group
    result['STATE'] = state

    return result

with Pool(8) as p:
    dataframe_list = p.starmap(task, combinations.iterrows())

# # Multi-processing is 5x faster!
# for index, row in combinations.iterrows():
#     result = task(index, row)
#     dataframe_list.append(result)


full_result = pd.concat(dataframe_list, axis=0)

full_result.to_csv("data/percentiles.csv", index=False)

print("Done")
