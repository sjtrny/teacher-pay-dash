import pandas as pd
import numpy as np
from rpy2.robjects.packages import importr
from rpy2.robjects import pandas2ri
import rpy2.rinterface as rinterface
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.utils.validation import check_is_fitted, check_array, check_X_y

pandas2ri.activate()

class PDFSmoother(BaseEstimator, RegressorMixin):
    binsmooth = importr('binsmooth')

    def fit(self, X, y, m=None):
        X, y = check_X_y(X, y, force_all_finite=False)
        if m is None:
            m = rinterface.NULL

        self.rlist_ = self.binsmooth.splinebins(X, y)
        self.rdict_ = dict(self.rlist_.items())

        self.func_ = self.rdict_['splinePDF']
        self.mean_ = self.rdict_['est_mean']

        return self

    def predict(self, X):
        check_is_fitted(self)
        X = check_array(X)

        return np.array(self.func_(X))


class InverseCDFSmoother(BaseEstimator, RegressorMixin):
    binsmooth = importr('binsmooth')

    def fit(self, X, y, m=None):
        X, y = check_X_y(X, y, force_all_finite=False)
        if m is None:
            m = rinterface.NULL

        self.rlist_ = self.binsmooth.splinebins(X, y, m)
        self.rdict_ = dict(self.rlist_.items())

        self.func_ = self.rdict_['splineInvCDF']
        self.mean_ = self.rdict_['est_mean'][0]

        return self

    def predict(self, X):
        check_is_fitted(self)
        X = check_array(X)

        return np.array(self.func_(X))


def get_percentiles(data):

    combinations = data[['OCCUPATION', 'AGE_GROUP', 'YEAR']].drop_duplicates()

    pcntile_range = np.arange(0, 101, 1).reshape(-1, 1) / 100

    dataframe_list = []

    for index, row in combinations.iterrows():
        year = row['YEAR']
        occ = row['OCCUPATION']
        age_group = row['AGE_GROUP']

        subset = data.query(f"OCCUPATION == '{occ}' and AGE_GROUP == '{age_group}'")
        subset = subset.sort_values("DECILE_LOW", ascending=True)

        smoother = InverseCDFSmoother()
        smoother.fit(subset["DECILE_HIGH"].values.reshape(-1, 1), subset["COUNT"])

        pcntile_vals = smoother.predict(pcntile_range)

        result = pd.concat(
            [
                pd.Series(np.full(pcntile_range.shape, year).squeeze(), name="YEAR"),
                pd.Series(np.full(pcntile_range.shape, occ).squeeze(), name="OCCUPATION"),
                pd.Series(np.full(pcntile_range.shape, age_group).squeeze(), name="AGE_GROUP"),
                pd.Series((pcntile_range.squeeze() * 100).astype(int), name="PERCENTILE"),
                pd.Series(pcntile_vals.squeeze(), name="PERCENTILE_VALUE"),
            ],
            axis=1
        )

        dataframe_list.append(result)

    full_result = pd.concat(dataframe_list, axis=0)

    full_result.to_csv("percentiles.csv", index=False)



