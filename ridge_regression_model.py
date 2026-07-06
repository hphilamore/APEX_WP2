import pandas as pd
import numpy as np
from read_excel_data_funcs import *
import re
import scipy
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import itertools
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score
import pickle


def load_series(data, sheet_name, col_name, year):

    # Load feature
    df = data[sheet_name].copy()

    # # Get the name of the first column
    # time_col = df.columns[0]

    # # Convert using column name 
    # df[time_col] = pd.to_datetime(df[time_col].astype(str), errors='coerce', dayfirst=True)

    # # Filter rows to select section of time series
    # df_by_year = df[df[time_col].dt.year == year] 

    # Filter column to include data from selected year only
    df.index = pd.to_datetime(df.index, format='%d/%m/%Y')

    df_by_year = df[df.index.year == year]


    # Extract the required column
    values = df_by_year[col_name].values

    return values  # return values


def all_subsets(lst):
    return [
        list(combo)
        for r in range(1, len(lst) + 1)
        for combo in itertools.combinations(lst, r)
    ]

# file_path="mfc_features.xlsx"

# Read all sheets into a dict of DataFrames
# mfc_features = pd.read_excel(file_path, sheet_name=None)


with open('mfc_features.pkl', 'rb') as f:
    mfc_features = pickle.load(f)

# print(type(mfc_features))
print(mfc_features['COD'])
# print(mfc_features['COD']['7) 10*10 -1'])

# # Get the first feature name in the nested dictionary {features : {mfc names : mfc data}} to pickle file
first_feature = next(iter(mfc_features))
mfc_names = mfc_features[first_feature].keys()
print(mfc_names)



# first_sheet = next(iter(mfc_features.values()))




# # Get the first sheet (DataFrame)
# first_sheet = next(iter(mfc_features.values()))


# print(type(first_sheet.index))
# print(first_sheet.index[:5])
# print(type(mfc_features['COD'].index))


# # Get column names
# columns = first_sheet.columns.tolist()[1:]

# MFC types to exclude from training and test data
# patterns_to_include = [
mfc_types_all = [
                        r"10\*10\s*AC",
                        r"20\*30\s*AC",
                        r"10\*10(?!\s*AC)",
                        r"20\*30(?!\s*AC)"
                        ]

# pattern_labels = {
mgc_types_regex_mappings = {
        r"10\*10\s*AC": "10x10_AC",
        r"20\*30\s*AC": "20x30_AC",
        r"10\*10(?!\s*AC)": "10x10",  # match 10*10 NOT followed by AC
        r"20\*30(?!\s*AC)": "20x30"     # match 20*30 NOT followed by AC
    }

# Resistance values to include in data
resistances_all = [0.1, 1, 3]

# Years to include in data
years_all = [2024, 2025]

# Variables to store analysis of data combinations that give best results
best_r2 = -float("inf")
best_config = None
results = []

def build_and_evaluate_ridge():
    # Try all possble combinations of MFCs, resistance values and section of data (2024/2025)
    for subset_mfc_types, subset_resistances, subset_years in itertools.product( all_subsets(mfc_types_all),
                                                                                 all_subsets(resistances_all),
                                                                                 all_subsets(years_all)):
        # print(subset_mfc_types, subset_resistances, subset_years)

        # Data structures to hold training/test data
        cod_data = []
        v_peak_data = []
        p_peak_data = []
        energy_data = []
        resistance_data = []

        # Filter MFC columns, skipping any that aren't in current subset 
        for col in mfc_names:
            if not any(re.search(p, col) for p in subset_mfc_types):
                continue

            # Filter selected data, selecting only years in current subset 
            # for year in subset_years:

                # Get features 
                # cod = load_series(mfc_features, 'COD', col, year)
            #     resistance = load_series(mfc_features, 'Resistance kOhms', col, year)
            #     v_peak = load_series(mfc_features, 'Vpeak mV', col, year)
            #     p_peak = load_series(mfc_features, 'Ppeak W', col, year)
            #     energy = load_series(mfc_features, 'Energy J', col, year)

                
#                 # Include only desired resistance values
#                 mask = np.isin(resistance, resistances)

#                 # Apply mask to all aligned series and add features to training data
#                 cod_data.extend(cod[mask])
#                 v_peak_data.extend(v_peak[mask])
#                 p_peak_data.extend(p_peak[mask])
#                 energy_data.extend(energy[mask])
#                 resistance_data.extend(resistance[mask])

#                 cod_values = cod[mask]


#         # Prepare features and labels
#         X = np.column_stack((v_peak_data, 
#                             p_peak_data, 
#                             energy_data, 
#                             resistance_data))

#         y = np.array(cod_data)

#         # Drop any NaN values in data
#         mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
#         X = X[mask]
#         y = y[mask]

#         # Must be at least 10 data points to be evaluated
#         # print(len(y))
#         if len(y) < 10:
#             continue

#         # Split into training and testing sets
#         X_train, X_test, y_train, y_test = train_test_split(
#             X, y, test_size=0.2, random_state=42
#         )

#         # Create ridge regression model
#         model = Ridge(alpha=1.0)

#         # Train the model
#         model.fit(X_train, y_train)

#         # Make predictions
#         y_pred = model.predict(X_test)

#         # Evaluate
#         mse = mean_squared_error(y_test, y_pred)
#         r2 = r2_score(y_test, y_pred)

#         # Store result
#         results.append({
#             "patterns": patterns,
#             "resistances": resistances,
#             "years": years,
#             "r2": r2,
#             "mse": mse,
#             "coefficients": model.coef_.copy(),
#             "intercept": model.intercept_,
#             "n_samples": len(y)
#             })

#     # Sort results by R² descending
#     results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

#     # Get top 5
#     top_5 = results_sorted[:5]

#     print("\nTop 5 configurations:\n")

#     for i, res in enumerate(top_5, 1):
#         print(f"--- Rank {i} ---")
#         print("MFC types:", [pattern_labels[p] for p in res["patterns"]])
#         # print("MFC types:", res["patterns"])
#         print("Resistances kOhm:", res["resistances"])
#         print("Years:", res["years"])
#         print("R²:", round(res["r2"], 4))
#         # print("MSE:", round(res["mse"], 2))
#         # print("N Samples:", res["n_samples"])
#         print("Terms:", "v_peak, p_peak, energy, resistance")
#         print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
#         print("Intercept:", res["intercept"])
#         print()


if __name__ == '__main__':

    build_and_evaluate_ridge()








