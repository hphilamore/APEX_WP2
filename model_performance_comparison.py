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
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import pickle


def extract_data_subset(data, sheet_name, col_name, year, resistance):

    # Load date-time index for selected mfc
    COD_date_time_index = data['COD date time index'][col_name].copy()

    # Load resistance data for selected mfc
    resistance_column = data['Resistance kOhms'][col_name].copy()

    # Load feature  for selected mfc
    feature = data[sheet_name][col_name].copy()

    # Filter column to include data from selected year and resistance only
    mask_cod = COD_date_time_index.year == year
    mask_resistance = [r == resistance for r in resistance_column]
    feature = [f for f, c, r in zip(feature, mask_cod, mask_resistance) if c and r]

    # print(len(feature))

    return feature


def all_subsets(lst):
    return [
        list(combo)
        for r in range(1, len(lst) + 1)
        for combo in itertools.combinations(lst, r)
    ]

def prepare_model_data(model_data, labels, features):

    # Create DataFrame from the dictionary to make it easier to remove NaN values
    df = pd.DataFrame({f: model_data[f] for f in labels + features})

    # Convert everything to numeric; invalid values become NaN
    df = df.apply(pd.to_numeric, errors='coerce')

    # Drop rows where any value is NaN
    df = df.dropna()

    # Create y and X data as numpy arrays
    y = df[labels].to_numpy()

    X = df[features].to_numpy()

    return y, X


def evaluate_model_performance(X, y, results, configuration, 
                               model_class, features, test_size, 
                               min_data_points, verbose=True):

    # Drop any configurations with less than minimum threshold
    if len(y) < min_data_points:
        if verbose==True:
            print('Skip config (number of data points below threshold)', configuration['subset_mfc_types'],
                configuration['subset_resistances'],
                configuration['subset_years'])
        return

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )

    # Scale all features to mean 0, std 1, to retain feature importance 
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Store scores to compare performance using different values of alpha
    scores = []

    alphas = np.logspace(-4, 4, 100)

    # Hyperparameter sweep to tune alpha for current configuration 
    for alpha in alphas:

        # model = model_class(alpha=1.0)
        model = model_class(alpha=alpha)

        # Train the model
        # model.fit(X_train, y_train)
        model.fit(X_train_scaled, y_train)

        # Make predictions
        # y_pred = model.predict(X_test)
        y_pred = model.predict(X_test_scaled)

        # Evaluate
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Store result
        scores.append({
            "mfc_types": configuration['subset_mfc_types'],
            "resistances": configuration['subset_resistances'],
            "years": configuration['subset_years'],
            "r2": r2,
            "mse": mse,
            "alpha": alpha,
            "coefficients": model.coef_.copy(),
            "intercept": model.intercept_,
            "feature_scales": scaler.scale_.copy(),
            "n_samples": len(y)
            })
        
    # Sort results by R² descending
    scores_sorted = sorted(scores, key=lambda x: x["r2"], reverse=True)

    if verbose==True:
        print('Keep config', configuration['subset_mfc_types'],
                configuration['subset_resistances'],
                configuration['subset_years'])
    
    # Store the best value for this configuration with hyperparameter tuning 
    results.append(scores_sorted[0])


# MFC types
# mfc_types_all = [
#                         r"10\*10\s*AC",     # Carbon veil + activated carbon
#                         r"20\*30\s*AC",
#                         r"10\*10(?!\s*AC)", # Carbon veil
#                         r"20\*30(?!\s*AC)"
#                         ]

mfc_types_regex_mappings = {
        r"10\*10\s*AC": "10x10_AC",
        r"20\*30\s*AC": "20x30_AC",
        r"10\*10(?!\s*AC)": "10x10",  # match 10*10 NOT followed by AC
        r"20\*30(?!\s*AC)": "20x30"     # match 20*30 NOT followed by AC
    }

# Resistance values to include in data
# resistances_all = [0.1, 1, 3]

# Years to include in data
# years_all = [2024, 2025]

# Variables to store analysis of data combinations that give best results
best_r2 = -float("inf")
best_config = None
results = []

# # Get stored feature data
# with open('mfc_features.pkl', 'rb') as f:
#     mfc_features = pickle.load(f)

# # Get the column / mfc names from the first dictionary in the nested dictionary of fetaures
# first_feature = next(iter(mfc_features))
# mfc_names = mfc_features[first_feature].keys()


def compare_input_data_performance(features, 
                                   mfc_types_all, 
                                   resistances_all, 
                                   years_all,
                                   verbose=True):
    
    # Get stored feature data
    with open('mfc_features.pkl', 'rb') as f:
        mfc_features = pickle.load(f)

    # Get the column / mfc names from the first dictionary in the nested dictionary of fetaures
    first_feature = next(iter(mfc_features))
    mfc_names = mfc_features[first_feature].keys()

    # Try all possble combinations of MFCs, resistance values and year section of data (2024/2025)
    for subset_mfc_types, subset_resistances, subset_years in itertools.product( all_subsets(mfc_types_all),
                                                                                 all_subsets(resistances_all),
                                                                                 all_subsets(years_all)):
        # print(subset_mfc_types, subset_resistances, subset_years)
        configuration = {'subset_mfc_types': subset_mfc_types,
                         'subset_resistances': subset_resistances,
                         'subset_years':subset_years}
        

        # Data structure to hold training/test data
        model_data = {k : [] for k in mfc_features}

        # Flag to determine wether results of this configuration are saved
        skip_configuration = False

        # Filter MFC columns, skipping any that aren't in current subset 
        for col in mfc_names:
            if not any(re.search(p, col) for p in subset_mfc_types):
                continue

            # Filter selected data to include only years and resistances in current subset 
            for year in subset_years:

                for resistance in subset_resistances:

                    for key in model_data:
                        # model_data[key].extend(extract_data_subset(mfc_features, key, col, year, resistance))
                        filtered_feature = extract_data_subset(mfc_features, key, col, year, resistance)
                        model_data[key].extend(filtered_feature)

                        # If configurations contains any combinations with zero data points, don't store result
                        if len(filtered_feature) == 0:
                            skip_configuration = True

        if skip_configuration == False:
        # print(len(model_data['COD']))
            # print(subset_mfc_types, subset_resistances, subset_years)

            # features=[
            #         # 'Vpeak mV', 
            #         #   'Ppeak W', 
            #           'Energy J', 
            #         #   'Resistance kOhms', 
            #         #   'Vfinal mV', 
            #         #   'Pfinal W'
            #         ]

            y, X = prepare_model_data(model_data, 
                                      labels=['COD'],
                                    #   features=['Vpeak mV', 'Ppeak W', 'Energy J', 'Resistance kOhms']
                                    #   features=['Vpeak mV', 'Ppeak W', 
                                    #             'Energy J', 'Resistance kOhms', 
                                    #             'Window length (hours)',
                                    #             'Vfinal mV', 'Pfinal W'
                                    #             ]
                                    features=features
                                      )        

            evaluate_model_performance(X, y, results, configuration, 
                                    # model=Ridge(alpha=1.0), 
                                    model_class=Ridge, 
                                    features=features,
                                    test_size=0.2, 
                                    min_data_points=25,
                                    verbose=verbose)
        else:
            if verbose==True:
                print('Skip config (redundant mfc type/resistance/year in config)', subset_mfc_types, subset_resistances, subset_years)

    # Sort results by R² descending
    results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

    # Get top 5
    top_3 = results_sorted[:3]

    best_config = results_sorted[0]

    # print("Best", best_config)

    if verbose == True:
        print("\nTop 3 configurations:\n")
        for i, res in enumerate(top_3, 1):
            print(f"--- Rank {i} ---")
            print()
            print("MFC types:", [mfc_types_regex_mappings[p] for p in res["mfc_types"]])
            # print("MFC types:", res["mfc_types"])
            print("Resistances kOhm:", res["resistances"])
            print("Years:", res["years"])
            print("R²:", round(res["r2"], 4))
            print("MSE:", round(res["mse"], 2))
            print("Alpha:", res["alpha"]),
            # print("N Samples:", res["n_samples"])
            # print("Terms:", "v_peak, p_peak, energy, resistance")
            print("Terms:", features)
            print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
            print("Intercept:", res["intercept"])
            print()

    return best_config



if __name__ == '__main__':
    compare_input_data_performance(
        features=[
            'Vpeak mV', 
            'Ppeak W', 
            'Energy J', 
            'Resistance kOhms', 
            'Vfinal mV', 
            'Pfinal W'
            ],
        mfc_types_all = [
            r"10\*10\s*AC",     # Carbon veil + activated carbon
            r"20\*30\s*AC",
            r"10\*10(?!\s*AC)", # Carbon veil
            r"20\*30(?!\s*AC)"
            ],
        resistances_all = [0.1, 1, 3],
        years_all = [2024, 2025]
    )








