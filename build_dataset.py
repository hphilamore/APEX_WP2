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


def load_series(data, sheet_name, col_name, year):

    # Load sheet
    df = data[sheet_name].copy()

    # Get the name of the first column
    time_col = df.columns[0]

    # Convert using column name 
    df[time_col] = pd.to_datetime(df[time_col].astype(str), errors='coerce', dayfirst=True)

    # Filter rows to select section of time series
    df_by_year = df[df[time_col].dt.year == year] 

    # Extract the required column
    values = df_by_year[col_name].values

    # return values, df_by_year.iloc[:, 0]  # return values + timestamps

    return values  # return values


def all_subsets(lst):
    return [
        list(combo)
        for r in range(1, len(lst) + 1)
        for combo in itertools.combinations(lst, r)
    ]

pattern_labels = {
        r"10\*10\s*AC": "10x10_AC",
        r"20\*30\s*AC": "20x30_AC",
        r"10\*10(?!\s*AC)": "10x10",  # match 10*10 NOT followed by AC
        r"20\*30(?!\s*AC)": "20x30"     # match 20*30 NOT followed by AC
    }

file_path="mfc_analysis.xlsx"

# Read all sheets into a dict of DataFrames
mfc_analysis = pd.read_excel(file_path, sheet_name=None)

# Get the first sheet (DataFrame)
first_sheet = next(iter(mfc_analysis.values()))

# Get column names
columns = first_sheet.columns.tolist()[1:]

print(columns)

# MFC types to exclude from training and test data
patterns_to_include = [
                        r"10\*10\s*AC",
                        # r"20\*30\s*AC",
                        r"10\*10(?!\s*AC)",
                        r"20\*30(?!\s*AC)"
                        ]

# Resistance values to include in data
resistances_to_include = [1, 3]

# Years to include in data
years_to_include = [2024, 2025]

print(all_subsets(years_to_include))


best_r2 = -float("inf")
best_config = None

results = []


for patterns, resistances, years in itertools.product(all_subsets(patterns_to_include),
                                                      all_subsets(resistances_to_include),
                                                      all_subsets(years_to_include)):

    # print(patterns, resistances, years)


    cod_data = []
    v_peak_data = []
    p_peak_data = []
    energy_data = []
    resistance_data = []
    time_cod_data = []

    for col in columns:
        
        # Include only desired MFC types  
        # if not any(re.search(p, col) for p in patterns_to_include):
        if not any(re.search(p, col) for p in patterns):
            continue

        # Select section of data by year
        # for year in years_to_include:
        for year in years:

            # Get features 
            # cod, time_cod = load_series(mfc_analysis, 'COD', col, year)
            # resistance, time_cod = load_series(mfc_analysis, 'Resistance kOhms', col, year)
            # v_peak, time_cod = load_series(mfc_analysis, 'Vpeak mV', col, year)
            # p_peak, time_cod = load_series(mfc_analysis, 'Ppeak W', col, year)
            # energy, time_cod = load_series(mfc_analysis, 'Energy J', col, year)

            cod = load_series(mfc_analysis, 'COD', col, year)
            resistance = load_series(mfc_analysis, 'Resistance kOhms', col, year)
            v_peak = load_series(mfc_analysis, 'Vpeak mV', col, year)
            p_peak = load_series(mfc_analysis, 'Ppeak W', col, year)
            energy = load_series(mfc_analysis, 'Energy J', col, year)

            # Include only desired resistance values
            # mask = np.isin(resistance, resistances_to_include)
            mask = np.isin(resistance, resistances)

            # Apply mask to all aligned series
            # cod        = cod[mask]
            # v_peak     = v_peak[mask]
            # p_peak     = p_peak[mask]
            # energy     = energy[mask]
            # resistance = resistance[mask]
            # time_cod   = time_cod[mask]

            # selected_events = cod[mask]
            # if all(x == selected_events[0] for x in selected_events):
            #     print("All elements are equal")
            #     # continue

            # else:



            # Apply mask to all aligned series and add features to training data
            cod_data.extend(cod[mask])
            v_peak_data.extend(v_peak[mask])
            p_peak_data.extend(p_peak[mask])
            energy_data.extend(energy[mask])
            resistance_data.extend(resistance[mask])

            cod_values = cod[mask]


            # cmap = plt.cm.magma   # choose a colormap
            # n = len(cod)          # number of loop iterations
            # colors = cmap(np.linspace(0, 1, n))

            # for a, b, c, d in zip(cod, v_peak, resistance, colors):

            #     if c == 0.1:
            #         m = '*'
            #     elif c == 1:
            #         m = 'o'
            #     else:
            #         m = 'v'

            #     # plt.scatter(a, b, marker=m, color=d)
            #     plt.scatter(a, b, marker=m)

            # plt.title(col)
            # plt.xlabel("COD")
            # plt.ylabel("Peak")
            # plt.show()


    # Prepare features and labels
    X = np.column_stack((v_peak_data, 
                         p_peak_data, 
                         energy_data, 
                         resistance_data))

    y = np.array(cod_data)

    # Drop any NaN values in data
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]

    # Must be at least 10 data points to be evaluated
    # print(len(y))
    if len(y) < 10:
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


    # print("Coefficients:", model.coef_)
    # print("Intercept:", model.intercept_)
    # print("Test MSE:", mse)
    # print("Test R^2:", r2)
    # print(model.score(X_train, y_train))
    # print(model.score(X_test, y_test))


    #  Track best
    # if r2 > best_r2:
    #     best_r2 = r2
    #     best_config = (patterns, resistances, years, model.coef_.copy(), cod_values)

    # print(f"{patterns}, {resistances}, {years}, {cod_values}→ R²={r2:.3f}")

    results.append({
        "patterns": patterns,
        "resistances": resistances,
        "years": years,
        "r2": r2,
        "mse": mse,
        "coefficients": model.coef_.copy(),
        "intercept": model.intercept_,
        "n_samples": len(y)
        })

# print("\nBest config:")
# print(best_config)
# print("Best R²:", best_r2)

# Sort results by R² descending
results_sorted = sorted(results, key=lambda x: x["r2"], reverse=True)

# Get top 5
top_5 = results_sorted[:5]

print("\nTop 5 configurations:\n")

for i, res in enumerate(top_5, 1):
    print(f"--- Rank {i} ---")
    print("MFC types:", [pattern_labels[p] for p in res["patterns"]])
    # print("MFC types:", res["patterns"])
    print("Resistances kOhm:", res["resistances"])
    print("Years:", res["years"])
    print("R²:", round(res["r2"], 4))
    # print("MSE:", round(res["mse"], 2))
    # print("N Samples:", res["n_samples"])
    print("Terms:", "v_peak, p_peak, energy, resistance")
    print("Coefficients:", [float(round(r, 3)) for r in res["coefficients"]])
    print("Intercept:", res["intercept"])
    print()











