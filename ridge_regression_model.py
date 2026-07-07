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


def extract_data_subset(data, sheet_name, col_name, year, resistance):

    # Load date-time index for selected mfc
    COD_date_time_index = data['COD date time index'][col_name].copy()

    # Load resistance data for selected mfc
    resistance_column = data['Resistance kOhms'][col_name].copy()

    # Load feature  for selected mfc
    feature = data[sheet_name][col_name].copy()

    # Filter column to include data from selected year only
    mask_cod = COD_date_time_index.year == year
    mask_resistance = [r == resistance for r in resistance_column]
    feature = [f for f, c, r in zip(feature, mask_cod, mask_resistance) if c and r]

    # print(col_name, year, resistance, len(feature))

    # print('Resistance', resistance)
    # print(resistance_column)
    # print(mask_cod)
    # print(mask_resistance)
    # print('final feature', feature)

    return feature


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
# print(mfc_features['COD'])
# print(mfc_features['COD']['7) 10*10 -1'])

# Get the column / mfc names from the first dictionary in the nested dictionary of fetaures
first_feature = next(iter(mfc_features))
mfc_names = mfc_features[first_feature].keys()
# print(mfc_names)

print(mfc_features.keys())

# MFC types
# patterns_to_include = [
mfc_types_all = [
                        r"10\*10\s*AC",
                        r"20\*30\s*AC",
                        r"10\*10(?!\s*AC)",
                        r"20\*30(?!\s*AC)"
                        ]

# pattern_labels = {
mfc_types_regex_mappings = {
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

        # Data structure to hold training/test data
        # cod_data = []
        # v_peak_data = []
        # p_peak_data = []
        # energy_data = []
        # resistance_data = []
        model_data = {k : [] for k in mfc_features}

        # Filter MFC columns, skipping any that aren't in current subset 
        for col in mfc_names:
            if not any(re.search(p, col) for p in subset_mfc_types):
                continue

            # Filter selected data to include only years and resistances in current subset 
            for year in subset_years:

                for resistance in subset_resistances:

                    # cod_data.extend(extract_data_subset(mfc_features, 'COD', col, year, resistance))
                    # resistance_data.extend(extract_data_subset(mfc_features, 'Resistance kOhms', col, year, resistance))
                    # v_peak_data.extend(extract_data_subset(mfc_features, 'Vpeak mV', col, year, resistance))
                    # p_peak_data.extend(extract_data_subset(mfc_features, 'Ppeak W', col, year, resistance))
                    # energy_data.extend(extract_data_subset(mfc_features, 'Energy J', col, year, resistance))
                    # print(col, year, resistance, ', N data points', len(cod_data))
                    for key in model_data:
                        model_data[key].extend(extract_data_subset(mfc_features, key, col, year, resistance))


        # print('Length of data for config', len(cod_data))
        # print()
        
        # print(v_peak_data)
        # print(model_data['COD'][:20])
                
        # Prepare features and labels
        labels_for_model = ['COD']
        features_for_model = ['Vpeak mV', 'Ppeak W', 'Energy J', 'Resistance kOhms']

        # Create DataFrame from the dictionary to make it easier to remove NaN values
        df = pd.DataFrame({f: model_data[f] for f in labels_for_model + features_for_model})

        # Convert everything to numeric; invalid values become NaN
        df = df.apply(pd.to_numeric, errors='coerce')

        # Drop rows where any value is NaN
        df = df.dropna()

        # Create y and X data as numpy arrays
        y = df[labels_for_model].to_numpy()

        X = df[features_for_model].to_numpy()



        # y = np.array(cod_data)

        # X = np.column_stack((v_peak_data, 
        #                      p_peak_data, 
        #                      energy_data, 
        #                      resistance_data))

        # y = np.array(model_data['COD'])

        # X = np.column_stack((model_data['Vpeak mV'], 
        #                 model_data['Ppeak W'], 
        #                 model_data['Energy J'], 
        #                 model_data['Resistance kOhms']))
        
        # print(y.shape)
        # print(X.shape)

        # print(model_data[['COD', 'Vpeak mV', 'Ppeak W', 'Energy J', 'Resistance kOhms']].dtypes)

        # for k, v in model_data.items():
        #     print(k, type(v))
        # Drop any NaN values in data
        # mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        # X = X[mask]
        # y = y[mask]

        # Drop any configurations with less than 10 data points
        # print(len(y))
        if len(y) < 50:
            continue

        # Split into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Create ridge regression model
        model = Ridge(alpha=1.0)

        # Train the model
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)

        # Evaluate
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store result
        results.append({
            "mfc_types": subset_mfc_types,
            "resistances": subset_resistances,
            "years": subset_years,
            "r2": r2,
            "mse": mse,
            "coefficients": model.coef_.copy(),
            "intercept": model.intercept_,
            "n_samples": len(y)
            })

    # Sort results by R² descending
    results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

    # Get top 5
    top_5 = results_sorted[:5]

    print("\nTop 5 configurations:\n")

    for i, res in enumerate(top_5, 1):
        print(f"--- Rank {i} ---")
        print("MFC types:", [mfc_types_regex_mappings[p] for p in res["mfc_types"]])
        # print("MFC types:", res["mfc_types"])
        print("Resistances kOhm:", res["resistances"])
        print("Years:", res["years"])
        print("R²:", round(res["r2"], 4))
        # print("MSE:", round(res["mse"], 2))
        # print("N Samples:", res["n_samples"])
        print("Terms:", "v_peak, p_peak, energy, resistance")
        print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
        print("Intercept:", res["intercept"])
        print()


if __name__ == '__main__':

    build_and_evaluate_ridge()








