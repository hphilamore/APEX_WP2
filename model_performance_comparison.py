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
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import cross_val_score
from xgboost import XGBRegressor
import pickle

mfc_types_regex_mappings = {
        r"10\*10\s*AC": "10x10_AC",
        r"20\*30\s*AC": "20x30_AC",
        r"10\*10(?!\s*AC)": "10x10",  # match 10*10 NOT followed by AC
        r"20\*30(?!\s*AC)": "20x30"     # match 20*30 NOT followed by AC
    }

def filter_feature_data(data, sheet_name, col_name, year, resistance):

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

    return feature


def all_subsets(lst):
    return [
        list(combo)
        for r in range(1, len(lst) + 1)
        for combo in itertools.combinations(lst, r)
    ]


def prepare_model_data(model_data, labels, features, test_size):

    # Create DataFrame from the dictionary to make it easier to remove NaN values
    df = pd.DataFrame({f: model_data[f] for f in labels + features})

    # Convert everything to numeric; invalid values become NaN
    df = df.apply(pd.to_numeric, errors='coerce')

    # Drop rows where any value is NaN
    df = df.dropna()

    # Create y and X data as numpy arrays
    y = df[labels].to_numpy()

    X = df[features].to_numpy()

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )       

    return X_train, X_test, y_train, y_test 


def evaluate_model_performance(X_train, 
                               X_test, 
                               y_train, 
                               y_test, 
                               configuration, 
                               results,
                               model_class, 
                               param_grid,
                               features,  
                               scale_features=False, 
                               verbose=True):
    

    # Scale all features to mean 0, std 1, to retain feature importance 
    if scale_features:
        scaler = StandardScaler()
        X_train_model = scaler.fit_transform(X_train)
        X_test_model = scaler.transform(X_test)
    else:
        scaler = None
        X_train_model = X_train
        X_test_model = X_test

    # Store scores to compare performance using different hyperparameter combinations 
    param_gridsearch_results = []

    # Tune hyperparameters for current configuration using grid search
    for params in param_grid:

        model = model_class(**params)

        # Train the model
        # model.fit(X_train, y_train)
        model.fit(X_train_model, y_train)

        # Make predictions
        # y_pred = model.predict(X_test)
        y_pred = model.predict(X_test_model)

        # Evaluate
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)

        # Store result for current hyperparameter combination 
        param_result = {
            "mfc_types": configuration['subset_mfc_types'],
            "resistances": configuration['subset_resistances'],
            "years": configuration['subset_years'],
            "features": features,
            "r2": r2,
            "mse": mse,
            "mae": mae,
            "model": model.__class__.__name__,
            "parameters": params,
            # "alpha": alpha,
            # "coefficients": model.coef_.copy(),
            # "intercept": model.intercept_,
            # "feature_scales": scaler.scale_.copy(),
            "n_samples": len(y_train) + len(y_pred)
            }
        
        # Store model-specific information
        if hasattr(model, "coef_"):
            param_result["coefficients"] = model.coef_.copy()
            param_result["intercept"] = model.intercept_

        if hasattr(model, "feature_importances_"):
            param_result["feature_importances"] = model.feature_importances_

        if scaler is not None:
            param_result["feature_scales"] = scaler.scale_
        
        param_gridsearch_results.append(param_result)

        
    # Sort results by R² descending
    param_gridsearch_sorted = sorted(param_gridsearch_results, key=lambda x: x["r2"], reverse=True)

    if verbose==True:
        print('Keep config', configuration['subset_mfc_types'],
                configuration['subset_resistances'],
                configuration['subset_years'])
    
    # Store the best value for this configuration with hyperparameter tuning 
    results.append(param_gridsearch_sorted[0])


def extract_best_configs(model_results, verbose=True):

    best_configs = []

    # for results in [results_ridge, results_xgboost]:
    for results in model_results:

        # Sort results by R² descending
        results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

        best_configs.append(results_sorted[0])

        print('Num results', len(results_sorted))

        # Show top 3 configurations 
        top_3 = results_sorted[:3]
        if verbose == True:

            print("\nTop 3 configurations:\n")
            for i, res in enumerate(top_3, 1):

                print(f"--- Rank {i} ---")
                print()
                print("Model:", res["model"])
                print("MFC types:", [mfc_types_regex_mappings[p] for p in res["mfc_types"]])
                # print("MFC types:", res["mfc_types"])
                print("Resistances kOhm:", res["resistances"])
                print("Years:", res["years"])
                print("R²:", round(res["r2"], 3))
                print("MSE:", round(res["mse"], 3))
                print("MAE:", round(res["mae"], 3))
                # print("Alpha:", res["alpha"]),
                print("Model Parameters:", ", ".join(f"{k}: {v:.3f}" for k, v in res["parameters"].items())),
                # print("N Samples:", res["n_samples"])
                # print("Terms:", "v_peak, p_peak, energy, resistance")
                print("Terms:", res["features"])
                print(res.keys())
                if "coefficients" in res:
                    print("Coefficients:", res["coefficients"])
                if "intercept" in res:
                    print("Intercept:", res["intercept"])
                if "feature_importances" in res:
                    print("Feature Importances:", res["feature_importances"])
                # print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
                # print("Intercept:", res["intercept"])
                print()
    return best_configs


def compare_input_data_configurations(features, 
                                      labels,
                                   mfc_types_all, # all mfc types to test in configurations 
                                   resistances_all, # all resistances to test in configurations 
                                   years_all, # all years to test in configurations 
                                #    test_size=0.2, 
                                   min_data_points=25,
                                   verbose=True):
    
    # Variables to store results of data combinations that give best performance 
    results_ridge = []
    results_xgboost = []
    
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
        

        # Flag to determine whether results of this configuration are saved
        skip_configuration = False

        # Data structure to hold data filtered for this configuration 
        configuration_data = {k : [] for k in mfc_features}

        # Filter MFC columns, skipping any that aren't in current configuration
        for col in mfc_names:
            if not any(re.search(p, col) for p in subset_mfc_types):
                continue

            # Filter selected data to include only years and resistances in current subset 
            for year in subset_years:

                for resistance in subset_resistances:

                    for key in configuration_data:
                        # model_data[key].extend(filter_feature_data(mfc_features, key, col, year, resistance))
                        filtered_feature = filter_feature_data(mfc_features, key, col, year, resistance)
                        configuration_data[key].extend(filtered_feature)

                        # If configurations contains any combinations with zero data points, don't store result
                        if len(filtered_feature) == 0:
                            skip_configuration = True

        if skip_configuration == False:

            # Drop any configurations with less than minimum threshold
            if len(configuration_data[labels[0]]) < min_data_points:
                if verbose==True:
                    print('Skip config (number of data points below threshold)', configuration['subset_mfc_types'],
                        configuration['subset_resistances'],
                        configuration['subset_years'])
                continue

            X_train, X_test, y_train, y_test = prepare_model_data(
                        configuration_data, 
                        labels=['COD'],
                        features=features,
                        test_size=0.2
                    ) 
            
            # --------------------------------------
            # ----- Evauluate ridge regression -----
            # --------------------------------------
            ridge_params = [
                {"alpha": a}
                for a in np.logspace(-4,4,100)
            ]
       
            evaluate_model_performance(X_train, 
                                       X_test, 
                                       y_train, 
                                       y_test, 
                                       configuration, 
                                        results=results_ridge, 
                                        model_class=Ridge, 
                                        features=features,
                                        param_grid=ridge_params,
                                        scale_features=True,
                                        verbose=verbose)
            
            # --------------------------------------
            # ----- Evauluate XGBoost -----
            # --------------------------------------
            
            xgb_params = []

            # for n_estimators in [100,300,500]:
            #     for max_depth in [2,3,5]:
            #         for learning_rate in [0.01,0.05,0.1]:

            for n_estimators in [30, 50, 100]:
                for max_depth in [2, 3, 4]:
                    for learning_rate in [0.1]:

                        xgb_params.append({
                            "n_estimators": n_estimators,
                            "max_depth": max_depth,
                            "learning_rate": learning_rate,
                            "random_state":42
                        })
            
       
            evaluate_model_performance(
                                    X_train,
                                    X_test,
                                    y_train,
                                    y_test,
                                    configuration,
                                    results=results_xgboost,
                                    model_class=XGBRegressor,
                                    param_grid=xgb_params,
                                    features=features,
                                    scale_features=False
                                )
            
        else:
            if verbose==True:
                print('Skip config (redundant mfc type/resistance/year in config)', subset_mfc_types, subset_resistances, subset_years)

    best_configs = extract_best_configs([results_ridge, results_xgboost],
                                        verbose=True)

    # best_configs = []

    # for results in [results_ridge, results_xgboost]:

    #     # Sort results by R² descending
    #     results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

    #     best_configs.append(results_sorted[0])

    #     print('Num results', len(results_sorted))

    #     # Show top 3 configurations 
    #     top_3 = results_sorted[:3]
    #     if verbose == True:

    #         print("\nTop 3 configurations:\n")
    #         for i, res in enumerate(top_3, 1):

    #             print(f"--- Rank {i} ---")
    #             print()
    #             print("Model:", res["model"])
    #             print("MFC types:", [mfc_types_regex_mappings[p] for p in res["mfc_types"]])
    #             # print("MFC types:", res["mfc_types"])
    #             print("Resistances kOhm:", res["resistances"])
    #             print("Years:", res["years"])
    #             print("R²:", round(res["r2"], 3))
    #             print("MSE:", round(res["mse"], 3))
    #             print("MAE:", round(res["mae"], 3))
    #             # print("Alpha:", res["alpha"]),
    #             print("Model Parameters:", ", ".join(f"{k}: {v:.3f}" for k, v in res["parameters"].items())),
    #             # print("N Samples:", res["n_samples"])
    #             # print("Terms:", "v_peak, p_peak, energy, resistance")
    #             print("Terms:", res["features"])
    #             print(res.keys())
    #             if "coefficients" in res:
    #                 print("Coefficients:", res["coefficients"])
    #             if "intercept" in res:
    #                 print("Intercept:", res["intercept"])
    #             if "feature_importances" in res:
    #                 print("Feature Importances:", res["feature_importances"])
    #             # print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
    #             # print("Intercept:", res["intercept"])
    #             print()

    return best_configs



if __name__ == '__main__':
    compare_input_data_configurations(
        features=[
            'Vpeak mV', 
            'Ppeak W', 
            'Energy J', 
            'Resistance kOhms', 
            # 'Vfinal mV', 
            # 'Pfinal W'
            ],
        labels=['COD'],
        mfc_types_all = [
            r"10\*10\s*AC",     # Carbon veil + activated carbon
            r"20\*30\s*AC",
            r"10\*10(?!\s*AC)", # Carbon veil
            r"20\*30(?!\s*AC)"
            ],
        # resistances_all = [0.1, 1, 3],
        resistances_all = [1],
        #years_all = [2024, 2025],
        years_all = [2024],#, 2025],
        verbose=True
    )







