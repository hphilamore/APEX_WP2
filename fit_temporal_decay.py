import pandas as pd
import numpy as np
from read_excel_data_funcs import *
import re
import scipy
from scipy.optimize import minimize
import matplotlib.pyplot as plt

file_path="mfc_analysis.xlsx"

# Read all sheets into a dict of DataFrames
mfc_analysis = pd.read_excel(file_path, sheet_name=None)


# Get the first sheet (DataFrame)
first_sheet = next(iter(mfc_analysis.values()))

# Get column names
columns = first_sheet.columns.tolist()[1:]

print(columns)


# print(mfc_analysis.keys())  # sheet names

patterns = {
        "10x10_AC": r"10\*10\s*AC",
        "20x30_AC": r"20\*30\s*AC",
        "10x10": r"10\*10(?!\s*AC)",   # match 10*10 NOT followed by AC
        "20x30": r"20\*30(?!\s*AC)"    # match 20*30 NOT followed by AC
    }


def load_series(data, sheet_name, col_name, year):

    # Load sheet
    df = data[sheet_name].copy()

    # Get the name of the first column
    time_col = df.columns[0]

    # Convert using column name 
    df[time_col] = pd.to_datetime(df[time_col].astype(str), errors='coerce', dayfirst=True)

    # Filter rows where year == 2024
    df_2024 = df[df[time_col].dt.year == year] 

    # Exclue last row (anomoly)
    # df_2024 = df_2024.iloc[:-1]

    # Extract the required column
    values = df_2024[col_name].values
    # values = df_2024[col].values

    return values, df_2024.iloc[:, 0]  # return values + timestamps

    # for label, pattern in patterns.items():
    #     print(f"\nPattern: {label}")

    #     for col in df.columns:
    #         if re.search(pattern, col):
    #             print(f"  -> {col}")




def simulate_health(cod, a, cod_crit):

    # Health
    h = np.zeros_like(cod)

    h[0] = 1.0  # assume healthy start

    for t in range(1, len(cod)):

        h[t] = h[t-1] + a * (cod[t] - cod_crit)

        h[t] = np.clip(h[t], 0.0, 1.0)

    return h


def loss(params, cod, resistance, peak):

    # a, cod_crit, gain, r_coeff = params
    a, cod_crit, gain = params

    # simulate health
    h = simulate_health(cod, a, cod_crit)

    # predict peak
    # peak_pred = gain * h * cod + r_coeff * resistance
    peak_pred = gain * h * cod * resistance

    # Mean squared error betweeen predicted peak and real peak using the input parameters
    mse = np.mean((peak - peak_pred)**2)

    return mse



def fit_model(cod, resistance, peak):

    result = minimize(
        loss,
        x0=[0.01, 
            np.mean(cod), 
            1.0, 
            # 0.1
            ],  # initial guesses
        args=(cod, resistance, peak),
        bounds=[
            (0, None),      # a ≥ 0
            (0, None),      # CODcrit ≥ 0
            (0, None),      # gain ≥ 0
            # (None, None)    # resistance coeff
        ]
    )

    return result.x

cmap = plt.cm.magma   # choose any colormap
n = len(columns)                  # number of loop iterations
colours = cmap(np.linspace(0, 1, n))

for col, e in zip(columns, colours):

    if re.search(r"20\*30\s*AC", col):
        continue

    y = 2024
    cod, time_cod = load_series(mfc_analysis, 'COD', col, year=y)
    resistance, time_cod = load_series(mfc_analysis, 'Resistance kOhms', col, year=y)
    v_peak, time_cod = load_series(mfc_analysis, 'Vpeak mV', col, year=y)
    p_peak, time_cod = load_series(mfc_analysis, 'Ppeak W', col, year=y)
    print(cod)

    cod_scaled = cod / np.max(cod)
    params = fit_model(cod_scaled, resistance, v_peak)


    # a_opt, codcrit_opt, gain_opt, r_opt = params
    a_opt, codcrit_opt, gain_opt = params

    print()
    print(col)
    print("a:", a_opt)
    print("CODcrit:", codcrit_opt)
    print("gain:", gain_opt)
    # print("resistance coeff:", r_opt)


    h = simulate_health(cod_scaled, a_opt, codcrit_opt)
    print(cod)
    print(v_peak)
    print(h)
    print(resistance)

    cmap = plt.cm.magma   # choose any colormap
    n = len(cod)                  # number of loop iterations
    colors = cmap(np.linspace(0, 1, n))

    for a,b,c, d in zip(cod, v_peak, resistance, colors):

        if c == 0.1:
            m = '*'
        elif c == 1:
            m = 'o'
        else:
            m = 'v'

        plt.scatter(a, b, marker=m, color=d)
        # plt.scatter(a, b, marker=m)

    plt.xlabel("COD")
    plt.ylabel("Peak")
    plt.show()















